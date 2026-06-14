"""
Internal API views for service-to-service communication
"""
import logging
from django.db.models import F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.responses import success_response, error_response
from .models import Post, PostEditHistory
from .serializers import PostListSerializer, PostCreateSerializer, PostUpdateSerializer

logger = logging.getLogger(__name__)


class InternalPostViewSet(viewsets.GenericViewSet):
    """内部服务视图集（仅供其他服务调用）"""

    queryset = Post.objects.filter(status=Post.STATUS_PUBLISHED)
    lookup_field = 'pk'

    @action(detail=True, methods=['post'], url_path='increment-views')
    def increment_views(self, request, pk=None):
        try:
            post = self.get_queryset().get(pk=pk)
            post.increment_views()
            return Response(success_response(data={'views_count': post.views_count}, message='浏览量已更新'))
        except Post.DoesNotExist:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

    @action(detail=True, methods=['post'], url_path='increment-replies')
    def increment_replies(self, request, pk=None):
        try:
            post = Post.objects.get(pk=pk)
            value = int(request.data.get('value', 1))
            Post.objects.filter(id=pk).update(replies_count=F('replies_count') + value)
            post.refresh_from_db()
            return Response(success_response(data={'replies_count': post.replies_count}, message='回复数已更新'))
        except Post.DoesNotExist:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

    @action(detail=True, methods=['post'], url_path='increment-likes')
    def increment_likes(self, request, pk=None):
        try:
            post = Post.objects.get(pk=pk)
            value = int(request.data.get('value', 1))
            Post.objects.filter(id=pk).update(likes_count=F('likes_count') + value)
            post.refresh_from_db()
            return Response(success_response(data={'likes_count': post.likes_count}, message='点赞数已更新'))
        except Post.DoesNotExist:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

    @action(detail=True, methods=['get'], url_path='validate')
    def validate_post(self, request, pk=None):
        try:
            post = self.get_queryset().get(pk=pk)
            return Response(success_response(data={
                'id': post.id, 'title': post.title, 'author_id': post.author_id,
                'section_id': post.section_id, 'status': post.status,
            }))
        except Post.DoesNotExist:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

    @action(detail=False, methods=['get'], url_path='batch')
    def batch_info(self, request):
        ids_param = request.query_params.get('ids', '')
        if not ids_param:
            resp, code = error_response('缺少 ids 参数', code=400, status_code=400)
            return Response(resp, status=code)
        try:
            ids = [int(i.strip()) for i in ids_param.split(',') if i.strip()]
        except (ValueError, TypeError):
            resp, code = error_response('ids 参数格式错误', code=400, status_code=400)
            return Response(resp, status=code)
        if len(ids) > 100:
            resp, code = error_response('单次最多查询100条', code=400, status_code=400)
            return Response(resp, status=code)
        posts = Post.objects.filter(id__in=ids, status=Post.STATUS_PUBLISHED)
        result = {}
        for p in posts:
            result[p.id] = {
                'id': p.id, 'title': p.title, 'author_id': p.author_id,
                'section_id': p.section_id,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'views_count': p.views_count,
            }
        return Response(success_response(data={'posts': result}))

    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的用户ID', code=400, status_code=400)
            return Response(resp, status=code)
        queryset = self.get_queryset().filter(author_id=user_id)
        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-views_count']
        queryset = queryset.order_by(ordering if ordering in allowed else '-created_at')
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        posts = queryset[start:end]
        serializer = PostListSerializer(posts, many=True)
        return Response(success_response(data={
            'count': total,
            'next': f'/internal/posts/by-user/{user_id}/?page={page + 1}' if end < total else None,
            'previous': f'/internal/posts/by-user/{user_id}/?page={page - 1}' if page > 1 else None,
            'results': serializer.data,
        }))

    def create(self, request):
        """创建帖子（供AI服务调用）"""
        serializer = PostCreateSerializer(data=request.data)
        if not serializer.is_valid():
            resp, code = error_response('参数校验失败', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)
        author_id = request.data.get('author_id')
        if not author_id:
            resp, code = error_response('缺少 author_id 参数', code=400, status_code=400)
            return Response(resp, status=code)
        post = serializer.save(author_id=int(author_id))
        # 直接更新板块帖子计数
        from apps.section.models import Section
        from django.db.models import F as DjangoF
        Section.objects.filter(id=post.section_id).update(posts_count=DjangoF('posts_count') + 1)
        return Response(success_response(data={
            'id': post.id, 'title': post.title, 'author_id': post.author_id,
            'section_id': post.section_id, 'status': post.status,
            'created_at': post.created_at.isoformat() if post.created_at else None,
        }, message='帖子创建成功'), status=201)

    @action(detail=False, methods=['put'], url_path='(?P<post_id>[^/.]+)')
    def update_post(self, request, post_id=None):
        """编辑帖子（供AI服务调用）"""
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)
        serializer = PostUpdateSerializer(post, data=request.data, partial=True)
        if not serializer.is_valid():
            resp, code = error_response('参数校验失败', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)
        PostEditHistory.objects.create(
            post=post, title=post.title, content=post.content,
            section_id=post.section_id, edited_by=request.data.get('author_id', 0),
        )
        serializer.save()
        post.record_edit(request.data.get('author_id', 0))
        return Response(success_response(data={
            'id': post.id, 'title': post.title, 'content': post.content,
            'section_id': post.section_id, 'edit_count': post.edit_count,
        }, message='帖子更新成功'))

    @action(detail=False, methods=['get'], url_path='list')
    def list_posts(self, request):
        """查询帖子列表（供AI服务调用）"""
        queryset = Post.objects.filter(status=Post.STATUS_PUBLISHED)
        section_id = request.query_params.get('section_id')
        if section_id:
            queryset = queryset.filter(section_id=int(section_id))
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        posts = queryset.order_by('-created_at')[start:end]
        serializer = PostListSerializer(posts, many=True)
        return Response(success_response(data={
            'count': total, 'page': page, 'page_size': page_size,
            'results': serializer.data,
        }))
