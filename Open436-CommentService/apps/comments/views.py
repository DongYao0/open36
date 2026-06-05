"""
Comment views
"""
import logging
import requests
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticated, IsAuthorOrAdmin, IsAdminUser, IsActiveUser
from apps.core.responses import success_response, error_response
from apps.core.consul_client import consul_client
from django.conf import settings

from .models import Reply, PostLike, PostFavorite, ReplyLike, ShareRecord, UserFollow, Topic, TopicFollow
from .serializers import (
    ReplyListSerializer, ReplyCreateSerializer, ReplyUpdateSerializer,
    PostLikeSerializer, PostFavoriteSerializer, FavoriteListSerializer
)

logger = logging.getLogger(__name__)


def _get_service_url(service_name, fallback_env):
    url = consul_client.discover_service(service_name)
    return url or getattr(settings, fallback_env, None)


def _batch_get_posts(post_ids):
    """批量获取帖子信息（调用 M3）"""
    if not post_ids:
        return {}
    try:
        url = _get_service_url('content-service', 'CONTENT_SERVICE_URL')
        if not url:
            return {}
        ids_str = ','.join(str(i) for i in post_ids)
        resp = requests.get(f'{url}/internal/posts/batch/', params={'ids': ids_str}, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('data', {}).get('posts', {})
    except Exception as e:
        logger.warning(f'Batch get posts failed: {e}')
    return {}


def _validate_post(post_id):
    """验证帖子是否存在（调用 M3）"""
    try:
        url = _get_service_url('content-service', 'CONTENT_SERVICE_URL')
        if not url:
            return True, None
        resp = requests.get(f'{url}/internal/posts/{post_id}/validate/', timeout=2)
        if resp.status_code == 200:
            return True, None
        return False, '帖子不存在'
    except Exception as e:
        logger.warning(f'Post validation failed: {e}')
        return True, None


def _update_user_stats(user_id, field, value):
    """更新用户统计（调用 M2）"""
    try:
        url = _get_service_url('user-service', 'USER_SERVICE_URL')
        if not url:
            return
        requests.post(
            f'{url}/internal/users/{user_id}/statistics/increment/',
            json={'field': field, 'value': value},
            timeout=2,
            headers={'X-Internal-API-Key': settings.INTERNAL_API_KEY}
        )
    except Exception as e:
        logger.warning(f'Update user stats failed: {e}')


def _update_post_count(post_id, field, value):
    """更新帖子计数（调用 M3 content-service）"""
    try:
        url = _get_service_url('content-service', 'CONTENT_SERVICE_URL')
        if not url:
            return
        requests.post(
            f'{url}/internal/posts/{post_id}/{field}/',
            json={'value': value},
            timeout=2,
            headers={'X-Internal-API-Key': settings.INTERNAL_API_KEY}
        )
    except Exception as e:
        logger.warning(f'Update post {field} failed: {e}')


class ReplyViewSet(viewsets.GenericViewSet):
    """回复视图集"""

    queryset = Reply.objects.all()
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), IsActiveUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsActiveUser(), IsAuthorOrAdmin()]
        return []

    def get_object(self):
        pk = self.kwargs.get(self.lookup_field)
        try:
            return self.get_queryset().get(pk=pk)
        except Reply.DoesNotExist:
            return None

    def list(self, request):
        """获取帖子的回复列表（管理员支持全量查询）"""
        is_admin = getattr(request, 'is_admin', False)
        post_id = request.query_params.get('post_id')

        queryset = self.get_queryset()

        if post_id:
            try:
                post_id = int(post_id)
            except (ValueError, TypeError):
                resp, code = error_response('无效的 post_id', code=400, status_code=400)
                return Response(resp, status=code)
            queryset = queryset.filter(post_id=post_id)
        elif not is_admin:
            resp, code = error_response('缺少 post_id 参数', code=400, status_code=400)
            return Response(resp, status=code)

        if not is_admin:
            # 普通用户只能看到未删除的回复，但作者可以看到自己的已删除回复
            user_id = getattr(request, 'user_id', None)
            if user_id:
                queryset = queryset.filter(
                    Q(is_deleted=False) | Q(author_id=user_id)
                )
            else:
                queryset = queryset.filter(is_deleted=False)
        else:
            # 管理员可按状态筛选
            status_filter = request.query_params.get('status')
            if status_filter == 'deleted':
                queryset = queryset.filter(is_deleted=True)
            elif status_filter == 'normal':
                queryset = queryset.filter(is_deleted=False)
            # 管理员搜索内容
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(content__icontains=search)

        queryset = queryset.order_by('floor_number', 'created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 50)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        replies = queryset[start:end]

        serializer = ReplyListSerializer(replies, many=True, context={'request': request})
        next_url = None
        prev_url = None
        if end < total:
            next_parts = [f'page={page + 1}']
            if post_id:
                next_parts.insert(0, f'post_id={post_id}')
            next_url = f'/api/replies/?{"&".join(next_parts)}'
        if page > 1:
            prev_parts = [f'page={page - 1}']
            if post_id:
                prev_parts.insert(0, f'post_id={post_id}')
            prev_url = f'/api/replies/?{"&".join(prev_parts)}'
        return Response(success_response(data={
            'count': total,
            'next': next_url,
            'previous': prev_url,
            'results': serializer.data,
        }))

    @transaction.atomic
    def create(self, request):
        """发布回复"""
        post_id = request.data.get('post_id')
        if not post_id:
            resp, code = error_response('缺少 post_id', code=400, status_code=400)
            return Response(resp, status=code)

        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的 post_id', code=400, status_code=400)
            return Response(resp, status=code)

        valid, err = _validate_post(post_id)
        if not valid:
            resp, code = error_response(err, code=400, status_code=400)
            return Response(resp, status=code)

        serializer = ReplyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        author_id = getattr(request, 'user_id', None)
        if not author_id:
            resp, code = error_response('未获取到用户信息', code=401, status_code=401)
            return Response(resp, status=code)

        # 验证父回复
        parent_id = serializer.validated_data.get('parent_id')
        if parent_id:
            try:
                parent = Reply.objects.get(pk=parent_id, post_id=post_id, is_deleted=False)
            except Reply.DoesNotExist:
                resp, code = error_response('父回复不存在', code=400, status_code=400)
                return Response(resp, status=code)

        # 计算楼层号
        last_floor = Reply.objects.filter(post_id=post_id).order_by('-floor_number').first()
        floor_number = (last_floor.floor_number + 1) if last_floor else 1

        reply = Reply.objects.create(
            post_id=post_id,
            author_id=author_id,
            parent_id=parent_id,
            content=serializer.validated_data['content'],
            floor_number=floor_number,
        )

        _update_user_stats(author_id, 'replies_count', 1)
        _update_post_count(post_id, 'increment-replies', 1)
        return Response(success_response(
            data=ReplyListSerializer(reply, context={'request': request}).data,
            message='回复成功'
        ), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """编辑回复"""
        reply = self.get_object()
        if not reply:
            resp, code = error_response('回复不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        if reply.is_deleted:
            resp, code = error_response('回复已删除', code=400, status_code=400)
            return Response(resp, status=code)

        is_admin = getattr(request, 'is_admin', False)
        user_id = getattr(request, 'user_id', None)

        if not reply.can_edit(user_id, is_admin):
            resp, code = error_response('超过编辑时限（5分钟）', code=400, status_code=400)
            return Response(resp, status=code)

        serializer = ReplyUpdateSerializer(reply, data=request.data, partial=True)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        serializer.save()
        reply.record_edit()

        return Response(success_response(
            data=ReplyListSerializer(reply, context={'request': request}).data,
            message='回复已更新'
        ))

    def destroy(self, request, pk=None):
        """删除回复（软删除）"""
        reply = self.get_object()
        if not reply:
            resp, code = error_response('回复不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        reply.soft_delete()
        _update_user_stats(reply.author_id, 'replies_count', -1)
        _update_post_count(reply.post_id, 'increment-replies', -1)
        return Response(success_response(message='回复已删除'))

    @action(detail=True, methods=['post'], url_path='like')
    def toggle_reply_like(self, request, pk=None):
        """评论点赞/取消点赞"""
        reply = self.get_object()
        if not reply:
            resp, code = error_response('回复不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)
        if not user_id:
            resp, code = error_response('未登录', code=401, status_code=401)
            return Response(resp, status=code)

        like, created = ReplyLike.objects.get_or_create(reply_id=pk, user_id=user_id)
        if not created:
            like.delete()
            likes_count = ReplyLike.objects.filter(reply_id=pk).count()
            return Response(success_response(data={'is_liked': False, 'likes_count': likes_count}, message='已取消点赞'))

        likes_count = ReplyLike.objects.filter(reply_id=pk).count()
        return Response(success_response(data={'is_liked': True, 'likes_count': likes_count}, message='点赞成功'))


class InteractionViewSet(viewsets.GenericViewSet):
    """互动视图集（点赞/收藏）"""

    def get_permissions(self):
        if self.action in ['toggle_like', 'toggle_favorite', 'my_favorites']:
            return [IsAuthenticated(), IsActiveUser()]
        return []

    @action(detail=False, methods=['get'], url_path='posts/(?P<post_id>[^/.]+)/interaction-status')
    def interaction_status(self, request, post_id=None):
        """查询当前用户对帖子的互动状态（点赞/收藏）"""
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)
        is_liked = False
        is_favorited = False

        if user_id:
            is_liked = PostLike.objects.filter(post_id=post_id, user_id=user_id).exists()
            is_favorited = PostFavorite.objects.filter(post_id=post_id, user_id=user_id).exists()

        likes_count = PostLike.objects.filter(post_id=post_id).count()
        favorites_count = PostFavorite.objects.filter(post_id=post_id).count()

        return Response(success_response(data={
            'is_liked': is_liked,
            'is_favorited': is_favorited,
            'likes_count': likes_count,
            'favorites_count': favorites_count,
        }))

    @action(detail=False, methods=['post'], url_path='posts/(?P<post_id>[^/.]+)/like')
    def toggle_like(self, request, post_id=None):
        """点赞/取消点赞"""
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)

        # 验证帖子
        valid, err = _validate_post(post_id)
        if not valid:
            resp, code = error_response(err, code=400, status_code=400)
            return Response(resp, status=code)

        like, created = PostLike.objects.get_or_create(post_id=post_id, user_id=user_id)

        if not created:
            # 已点赞，取消点赞
            like.delete()
            _update_user_stats(user_id, 'likes_received', -1)
            _update_post_count(post_id, 'increment-likes', -1)
            likes_count = PostLike.objects.filter(post_id=post_id).count()
            return Response(success_response(data={'is_liked': False, 'likes_count': likes_count}, message='已取消点赞'))

        # 新增点赞
        _update_user_stats(user_id, 'likes_received', 1)
        _update_post_count(post_id, 'increment-likes', 1)
        likes_count = PostLike.objects.filter(post_id=post_id).count()
        return Response(success_response(data={'is_liked': True, 'likes_count': likes_count}, message='点赞成功'))

    @action(detail=False, methods=['post'], url_path='posts/(?P<post_id>[^/.]+)/favorite')
    def toggle_favorite(self, request, post_id=None):
        """收藏/取消收藏"""
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)

        valid, err = _validate_post(post_id)
        if not valid:
            resp, code = error_response(err, code=400, status_code=400)
            return Response(resp, status=code)

        fav, created = PostFavorite.objects.get_or_create(post_id=post_id, user_id=user_id)

        if not created:
            fav.delete()
            _update_user_stats(user_id, 'favorites_received', -1)
            return Response(success_response(data={'is_favorited': False}, message='已取消收藏'))

        _update_user_stats(user_id, 'favorites_received', 1)
        return Response(success_response(data={'is_favorited': True}, message='收藏成功'))

    @action(detail=False, methods=['get'], url_path='favorites')
    def my_favorites(self, request):
        """我的收藏列表"""
        user_id = getattr(request, 'user_id', None)

        queryset = PostFavorite.objects.filter(user_id=user_id).order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        favorites = queryset[start:end]

        # 批量获取帖子信息
        post_ids = [f.post_id for f in favorites]
        posts_map = _batch_get_posts(post_ids)

        results = []
        for fav in favorites:
            post_info = posts_map.get(str(fav.post_id), {})
            results.append({
                'id': fav.id,
                'post_id': fav.post_id,
                'title': post_info.get('title', ''),
                'author_id': post_info.get('author_id'),
                'section_id': post_info.get('section_id'),
                'views_count': post_info.get('views_count', 0),
                'created_at': fav.created_at,
                'post_created_at': post_info.get('created_at'),
            })

        return Response(success_response(data={
            'count': total,
            'next': f'/api/favorites/?page={page + 1}' if end < total else None,
            'previous': f'/api/favorites/?page={page - 1}' if page > 1 else None,
            'results': results,
        }))


class ShareViewSet(viewsets.GenericViewSet):
    """分享视图集"""

    @action(detail=False, methods=['post'], url_path='posts/(?P<post_id>[^/.]+)/share')
    def record_share(self, request, post_id=None):
        """记录分享"""
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)

        share_type = request.data.get('share_type', 'link')
        user_id = getattr(request, 'user_id', None)

        ShareRecord.objects.create(
            post_id=post_id,
            user_id=user_id,
            share_type=share_type,
        )

        share_count = ShareRecord.objects.filter(post_id=post_id).count()
        return Response(success_response(data={'share_count': share_count}, message='分享已记录'))

    @action(detail=False, methods=['get'], url_path='posts/(?P<post_id>[^/.]+)/share-count')
    def share_count(self, request, post_id=None):
        """获取分享数"""
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)

        count = ShareRecord.objects.filter(post_id=post_id).count()
        return Response(success_response(data={'post_id': post_id, 'share_count': count}))


class FollowViewSet(viewsets.GenericViewSet):
    """用户关注视图集"""

    def get_permissions(self):
        if self.action in ['toggle_follow', 'my_following', 'my_followers']:
            return [IsAuthenticated(), IsActiveUser()]
        return []

    @action(detail=False, methods=['post'], url_path='users/(?P<target_id>[^/.]+)/toggle')
    def toggle_follow(self, request, target_id=None):
        """关注/取消关注用户"""
        try:
            target_id = int(target_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的用户ID', code=400, status_code=400)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)
        if user_id == target_id:
            resp, code = error_response('不能关注自己', code=400, status_code=400)
            return Response(resp, status=code)

        follow, created = UserFollow.objects.get_or_create(
            follower_id=user_id, following_id=target_id
        )
        if not created:
            follow.delete()
            return Response(success_response(data={'is_following': False}, message='已取消关注'))

        return Response(success_response(data={'is_following': True}, message='关注成功'))

    @action(detail=False, methods=['get'], url_path='users/(?P<target_id>[^/.]+)/status')
    def follow_status(self, request, target_id=None):
        """查询关注状态"""
        try:
            target_id = int(target_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的用户ID', code=400, status_code=400)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)
        is_following = False
        if user_id:
            is_following = UserFollow.objects.filter(
                follower_id=user_id, following_id=target_id
            ).exists()

        followers_count = UserFollow.objects.filter(following_id=target_id).count()
        following_count = UserFollow.objects.filter(follower_id=target_id).count()

        return Response(success_response(data={
            'is_following': is_following,
            'followers_count': followers_count,
            'following_count': following_count,
        }))

    @action(detail=False, methods=['get'], url_path='my-following')
    def my_following(self, request):
        """我关注的用户列表"""
        user_id = getattr(request, 'user_id', None)
        queryset = UserFollow.objects.filter(follower_id=user_id).order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        follows = queryset[start:end]

        results = [{'user_id': f.following_id, 'created_at': f.created_at} for f in follows]
        return Response(success_response(data={
            'count': total,
            'next': f'/api/follows/my-following/?page={page + 1}' if end < total else None,
            'previous': f'/api/follows/my-following/?page={page - 1}' if page > 1 else None,
            'results': results,
        }))

    @action(detail=False, methods=['get'], url_path='my-followers')
    def my_followers(self, request):
        """我的粉丝列表"""
        user_id = getattr(request, 'user_id', None)
        queryset = UserFollow.objects.filter(following_id=user_id).order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        follows = queryset[start:end]

        results = [{'user_id': f.follower_id, 'created_at': f.created_at} for f in follows]
        return Response(success_response(data={
            'count': total,
            'next': f'/api/follows/my-followers/?page={page + 1}' if end < total else None,
            'previous': f'/api/follows/my-followers/?page={page - 1}' if page > 1 else None,
            'results': results,
        }))


class TopicViewSet(viewsets.GenericViewSet):
    """话题视图集"""

    queryset = Topic.objects.all()

    def get_permissions(self):
        if self.action in ['toggle_follow_topic', 'my_topics']:
            return [IsAuthenticated(), IsActiveUser()]
        return []

    def list(self, request):
        """话题列表"""
        queryset = Topic.objects.all().order_by('-posts_count')

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        topics = queryset[start:end]

        results = [{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'posts_count': t.posts_count,
            'followers_count': t.followers_count,
        } for t in topics]

        return Response(success_response(data={
            'count': total,
            'next': f'/api/topics/?page={page + 1}' if end < total else None,
            'previous': f'/api/topics/?page={page - 1}' if page > 1 else None,
            'results': results,
        }))

    @action(detail=True, methods=['post'], url_path='follow')
    def toggle_follow_topic(self, request, pk=None):
        """关注/取消关注话题"""
        try:
            topic = Topic.objects.get(pk=pk)
        except Topic.DoesNotExist:
            resp, code = error_response('话题不存在', code=404, status_code=404)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)
        follow, created = TopicFollow.objects.get_or_create(
            user_id=user_id, topic_id=pk
        )
        if not created:
            follow.delete()
            topic.followers_count = max(0, topic.followers_count - 1)
            topic.save(update_fields=['followers_count'])
            return Response(success_response(data={'is_following': False}, message='已取消关注'))

        topic.followers_count += 1
        topic.save(update_fields=['followers_count'])
        return Response(success_response(data={'is_following': True}, message='关注成功'))

    @action(detail=True, methods=['get'], url_path='follow-status')
    def topic_follow_status(self, request, pk=None):
        """查询话题关注状态"""
        user_id = getattr(request, 'user_id', None)
        is_following = False
        if user_id:
            is_following = TopicFollow.objects.filter(user_id=user_id, topic_id=pk).exists()

        try:
            topic = Topic.objects.get(pk=pk)
            followers_count = topic.followers_count
        except Topic.DoesNotExist:
            followers_count = 0

        return Response(success_response(data={
            'is_following': is_following,
            'followers_count': followers_count,
        }))

    @action(detail=False, methods=['get'], url_path='my-topics')
    def my_topics(self, request):
        """我关注的话题"""
        user_id = getattr(request, 'user_id', None)
        follows = TopicFollow.objects.filter(user_id=user_id).order_by('-created_at')
        topic_ids = [f.topic_id for f in follows]
        topics = Topic.objects.filter(id__in=topic_ids)

        results = [{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'posts_count': t.posts_count,
            'followers_count': t.followers_count,
        } for t in topics]

        return Response(success_response(data={'results': results}))
