"""
Comment views — 合并后 HTTP 内部调用改为 ORM 直查
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
from django.conf import settings

from .models import Reply, PostLike, PostFavorite, ReplyLike, ShareRecord, UserFollow, Topic, TopicFollow
from .serializers import (
    ReplyListSerializer, ReplyCreateSerializer, ReplyUpdateSerializer,
    PostLikeSerializer, PostFavoriteSerializer, FavoriteListSerializer
)

logger = logging.getLogger(__name__)


def _validate_post(post_id):
    """验证帖子是否存在（直接 ORM 查询）"""
    from apps.content.models import Post
    try:
        Post.objects.get(pk=post_id, status=Post.STATUS_PUBLISHED)
        return True, None
    except Post.DoesNotExist:
        return False, '帖子不存在'


def _batch_get_posts(post_ids):
    """批量获取帖子信息（直接 ORM 查询）"""
    from apps.content.models import Post
    if not post_ids:
        return {}
    posts = Post.objects.filter(id__in=post_ids, status=Post.STATUS_PUBLISHED)
    result = {}
    for p in posts:
        result[str(p.id)] = {
            'id': p.id, 'title': p.title, 'author_id': p.author_id,
            'section_id': p.section_id,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'views_count': p.views_count,
        }
    return result


def _update_user_stats(user_id, field, value):
    """更新用户统计（调用 Auth 服务）"""
    try:
        from apps.core.consul_client import consul_client
        url = consul_client.discover_service('auth-service')
        if not url:
            url = getattr(settings, 'AUTH_SERVICE_URL', None)
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
    """更新帖子计数（直接 ORM 操作）"""
    from apps.content.models import Post
    try:
        if field == 'increment-replies':
            Post.objects.filter(id=post_id).update(replies_count=F('replies_count') + value)
        elif field == 'increment-likes':
            Post.objects.filter(id=post_id).update(likes_count=F('likes_count') + value)
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
        """获取帖子的回复列表"""
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
            user_id = getattr(request, 'user_id', None)
            if user_id:
                queryset = queryset.filter(Q(is_deleted=False) | Q(author_id=user_id))
            else:
                queryset = queryset.filter(is_deleted=False)
        else:
            status_filter = request.query_params.get('status')
            if status_filter == 'deleted':
                queryset = queryset.filter(is_deleted=True)
            elif status_filter == 'normal':
                queryset = queryset.filter(is_deleted=False)
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
            'count': total, 'next': next_url, 'previous': prev_url,
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

        parent_id = serializer.validated_data.get('parent_id')
        if parent_id:
            try:
                Reply.objects.get(pk=parent_id, post_id=post_id, is_deleted=False)
            except Reply.DoesNotExist:
                resp, code = error_response('父回复不存在', code=400, status_code=400)
                return Response(resp, status=code)

        last_floor = Reply.objects.filter(post_id=post_id).order_by('-floor_number').first()
        floor_number = (last_floor.floor_number + 1) if last_floor else 1

        reply = Reply.objects.create(
            post_id=post_id, author_id=author_id, parent_id=parent_id,
            content=serializer.validated_data['content'], floor_number=floor_number,
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
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)
        user_id = getattr(request, 'user_id', None)
        is_liked = PostLike.objects.filter(post_id=post_id, user_id=user_id).exists() if user_id else False
        is_favorited = PostFavorite.objects.filter(post_id=post_id, user_id=user_id).exists() if user_id else False
        return Response(success_response(data={
            'is_liked': is_liked, 'is_favorited': is_favorited,
            'likes_count': PostLike.objects.filter(post_id=post_id).count(),
            'favorites_count': PostFavorite.objects.filter(post_id=post_id).count(),
        }))

    @action(detail=False, methods=['post'], url_path='posts/(?P<post_id>[^/.]+)/like')
    def toggle_like(self, request, post_id=None):
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
        like, created = PostLike.objects.get_or_create(post_id=post_id, user_id=user_id)
        if not created:
            like.delete()
            _update_user_stats(user_id, 'likes_received', -1)
            _update_post_count(post_id, 'increment-likes', -1)
            return Response(success_response(data={'is_liked': False, 'likes_count': PostLike.objects.filter(post_id=post_id).count()}, message='已取消点赞'))
        _update_user_stats(user_id, 'likes_received', 1)
        _update_post_count(post_id, 'increment-likes', 1)
        return Response(success_response(data={'is_liked': True, 'likes_count': PostLike.objects.filter(post_id=post_id).count()}, message='点赞成功'))

    @action(detail=False, methods=['post'], url_path='posts/(?P<post_id>[^/.]+)/favorite')
    def toggle_favorite(self, request, post_id=None):
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
        user_id = getattr(request, 'user_id', None)
        queryset = PostFavorite.objects.filter(user_id=user_id).order_by('-created_at')
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        favorites = queryset[start:end]
        post_ids = [f.post_id for f in favorites]
        posts_map = _batch_get_posts(post_ids)
        results = []
        for fav in favorites:
            post_info = posts_map.get(str(fav.post_id), {})
            results.append({
                'id': fav.id, 'post_id': fav.post_id,
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
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)
        share_type = request.data.get('share_type', 'link')
        user_id = getattr(request, 'user_id', None)
        ShareRecord.objects.create(post_id=post_id, user_id=user_id, share_type=share_type)
        return Response(success_response(data={'share_count': ShareRecord.objects.filter(post_id=post_id).count()}, message='分享已记录'))

    @action(detail=False, methods=['get'], url_path='posts/(?P<post_id>[^/.]+)/share-count')
    def share_count(self, request, post_id=None):
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)
        return Response(success_response(data={'post_id': post_id, 'share_count': ShareRecord.objects.filter(post_id=post_id).count()}))


class FollowViewSet(viewsets.GenericViewSet):
    """用户关注视图集"""

    def get_permissions(self):
        if self.action in ['toggle_follow', 'my_following', 'my_followers']:
            return [IsAuthenticated(), IsActiveUser()]
        return []

    @action(detail=False, methods=['post'], url_path='users/(?P<target_id>[^/.]+)/toggle')
    def toggle_follow(self, request, target_id=None):
        try:
            target_id = int(target_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的用户ID', code=400, status_code=400)
            return Response(resp, status=code)
        user_id = getattr(request, 'user_id', None)
        if user_id == target_id:
            resp, code = error_response('不能关注自己', code=400, status_code=400)
            return Response(resp, status=code)
        follow, created = UserFollow.objects.get_or_create(follower_id=user_id, following_id=target_id)
        if not created:
            follow.delete()
            return Response(success_response(data={'is_following': False}, message='已取消关注'))
        return Response(success_response(data={'is_following': True}, message='关注成功'))

    @action(detail=False, methods=['get'], url_path='users/(?P<target_id>[^/.]+)/status')
    def follow_status(self, request, target_id=None):
        try:
            target_id = int(target_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的用户ID', code=400, status_code=400)
            return Response(resp, status=code)
        user_id = getattr(request, 'user_id', None)
        is_following = UserFollow.objects.filter(follower_id=user_id, following_id=target_id).exists() if user_id else False
        return Response(success_response(data={
            'is_following': is_following,
            'followers_count': UserFollow.objects.filter(following_id=target_id).count(),
            'following_count': UserFollow.objects.filter(follower_id=target_id).count(),
        }))

    @action(detail=False, methods=['get'], url_path='my-following')
    def my_following(self, request):
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
        results = [{'id': t.id, 'name': t.name, 'description': t.description, 'posts_count': t.posts_count, 'followers_count': t.followers_count} for t in topics]
        return Response(success_response(data={
            'count': total,
            'next': f'/api/topics/?page={page + 1}' if end < total else None,
            'previous': f'/api/topics/?page={page - 1}' if page > 1 else None,
            'results': results,
        }))

    @action(detail=True, methods=['post'], url_path='follow')
    def toggle_follow_topic(self, request, pk=None):
        try:
            topic = Topic.objects.get(pk=pk)
        except Topic.DoesNotExist:
            resp, code = error_response('话题不存在', code=404, status_code=404)
            return Response(resp, status=code)
        user_id = getattr(request, 'user_id', None)
        follow, created = TopicFollow.objects.get_or_create(user_id=user_id, topic_id=pk)
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
        user_id = getattr(request, 'user_id', None)
        is_following = TopicFollow.objects.filter(user_id=user_id, topic_id=pk).exists() if user_id else False
        try:
            topic = Topic.objects.get(pk=pk)
            followers_count = topic.followers_count
        except Topic.DoesNotExist:
            followers_count = 0
        return Response(success_response(data={'is_following': is_following, 'followers_count': followers_count}))

    @action(detail=False, methods=['get'], url_path='my-topics')
    def my_topics(self, request):
        user_id = getattr(request, 'user_id', None)
        follows = TopicFollow.objects.filter(user_id=user_id).order_by('-created_at')
        topic_ids = [f.topic_id for f in follows]
        topics = Topic.objects.filter(id__in=topic_ids)
        results = [{'id': t.id, 'name': t.name, 'description': t.description, 'posts_count': t.posts_count, 'followers_count': t.followers_count} for t in topics]
        return Response(success_response(data={'results': results}))
