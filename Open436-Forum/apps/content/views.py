"""
Post views — 合并后 HTTP 内部调用改为 ORM 直查
"""
import logging
import requests
from django.db import transaction
from django.db.models import F
from django.core.cache import cache
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticated, IsAuthorOrAdmin, IsAdminUser, IsActiveUser
from apps.core.responses import success_response, error_response
from django.conf import settings

from .models import Post, PostEditHistory
from .serializers import (
    PostListSerializer, PostDetailSerializer, PostCreateSerializer,
    PostUpdateSerializer, PostEditHistorySerializer
)

logger = logging.getLogger(__name__)


def _validate_section(section_id):
    """验证板块是否存在（直接 ORM 查询，不再走 HTTP）"""
    from apps.section.models import Section
    try:
        Section.objects.get(id=section_id, is_enabled=True)
        return True, None
    except Section.DoesNotExist:
        return False, '板块不存在或已禁用'


def _update_section_posts(section_id, value):
    """更新板块帖子数（直接 ORM 操作）"""
    from apps.section.models import Section
    try:
        Section.objects.filter(id=section_id).update(posts_count=F('posts_count') + value)
    except Exception as e:
        logger.warning(f'Update section posts count failed: {e}')


def _update_user_stats(user_id, field, value):
    """更新用户统计（调用 Auth 服务 —— 仍走 HTTP）"""
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


class PostViewSet(viewsets.GenericViewSet):
    """帖子视图集"""

    queryset = Post.objects.all()
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), IsActiveUser()]
        if self.action in ['update', 'partial_update', 'destroy', 'restore']:
            return [IsAuthenticated(), IsActiveUser(), IsAuthorOrAdmin()]
        if self.action in ['pin', 'unpin', 'history']:
            return [IsAdminUser()]
        return []

    def get_object(self):
        pk = self.kwargs.get(self.lookup_field)
        try:
            return self.get_queryset().get(pk=pk)
        except Post.DoesNotExist:
            return None

    def _get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')

    def list(self, request):
        """帖子列表（支持板块筛选、管理员全量查询）"""
        is_admin = getattr(request, 'is_admin', False)
        queryset = self.get_queryset()

        if not is_admin:
            queryset = queryset.filter(status=Post.STATUS_PUBLISHED)
        else:
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(title__icontains=search)

        section_id = request.query_params.get('section_id')
        if section_id:
            queryset = queryset.filter(section_id=int(section_id))

        ordering = request.query_params.get('ordering', '-created_at')
        allowed_ordering = ['-created_at', 'created_at', '-views_count', 'views_count']
        if ordering in allowed_ordering:
            queryset = queryset.order_by('-is_pinned', ordering)
        else:
            queryset = queryset.order_by('-is_pinned', '-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        posts = queryset[start:end]

        serializer = PostListSerializer(posts, many=True)
        return Response(success_response(data={
            'count': total,
            'next': f'/api/posts/?page={page + 1}' if end < total else None,
            'previous': f'/api/posts/?page={page - 1}' if page > 1 else None,
            'results': serializer.data,
        }))

    def create(self, request):
        """发布帖子"""
        serializer = PostCreateSerializer(data=request.data)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        section_id = serializer.validated_data['section_id']
        valid, err = _validate_section(section_id)
        if not valid:
            resp, code = error_response(err, code=400, status_code=400)
            return Response(resp, status=code)

        author_id = getattr(request, 'user_id', None)
        if not author_id:
            resp, code = error_response('未获取到用户信息', code=401, status_code=401)
            return Response(resp, status=code)

        post = Post.objects.create(
            title=serializer.validated_data['title'],
            content=serializer.validated_data['content'],
            author_id=author_id,
            section_id=section_id,
        )

        _update_user_stats(author_id, 'posts_count', 1)
        _update_section_posts(section_id, 1)

        return Response(success_response(
            data=PostDetailSerializer(post, context={'request': request}).data,
            message='帖子发布成功'
        ), status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """帖子详情"""
        post = self.get_object()
        if not post:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        if post.status == Post.STATUS_DELETED and not getattr(request, 'is_admin', False):
            resp, code = error_response('帖子已删除', code=40401, status_code=404)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)
        client_ip = self._get_client_ip(request)
        cache_key = f'post_view:{post.id}:uid:{user_id}:ip:{client_ip}'
        if not cache.get(cache_key) and user_id != post.author_id:
            post.increment_views()
            cache.set(cache_key, True, 600)

        return Response(success_response(
            data=PostDetailSerializer(post, context={'request': request}).data
        ))

    @transaction.atomic
    def update(self, request, pk=None):
        """编辑帖子"""
        post = self.get_object()
        if not post:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        if post.status == Post.STATUS_DELETED:
            resp, code = error_response('帖子已删除，无法编辑', code=400, status_code=400)
            return Response(resp, status=code)

        is_admin = getattr(request, 'is_admin', False)
        user_id = getattr(request, 'user_id', None)

        if not post.can_edit(user_id, is_admin):
            resp, code = error_response('超过编辑次数限制', code=400, status_code=400)
            return Response(resp, status=code)

        PostEditHistory.objects.create(
            post=post, title=post.title, content=post.content,
            section_id=post.section_id, edited_by=user_id,
        )

        serializer = PostUpdateSerializer(post, data=request.data, partial=True)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        if 'section_id' in serializer.validated_data:
            valid, err = _validate_section(serializer.validated_data['section_id'])
            if not valid:
                resp, code = error_response(err, code=400, status_code=400)
                return Response(resp, status=code)

        serializer.save()
        post.record_edit(user_id)

        return Response(success_response(
            data=PostDetailSerializer(post, context={'request': request}).data,
            message='帖子已更新'
        ))

    @transaction.atomic
    def destroy(self, request, pk=None):
        """删除帖子（软删除）"""
        post = self.get_object()
        if not post:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        post.soft_delete()
        _update_user_stats(post.author_id, 'posts_count', -1)
        _update_section_posts(post.section_id, -1)

        return Response(success_response(message='帖子已删除'))

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, pk=None):
        """恢复帖子（管理员）"""
        post = self.get_object()
        if not post:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)
        if post.status != Post.STATUS_DELETED:
            resp, code = error_response('帖子未删除', code=400, status_code=400)
            return Response(resp, status=code)
        post.restore()
        _update_user_stats(post.author_id, 'posts_count', 1)
        return Response(success_response(message='帖子已恢复'))

    @action(detail=True, methods=['post'], url_path='pin')
    def pin(self, request, pk=None):
        """置顶帖子（管理员）"""
        post = self.get_object()
        if not post:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)
        pin_type = request.data.get('pin_type', Post.PIN_GLOBAL)
        if pin_type not in [Post.PIN_GLOBAL, Post.PIN_SECTION]:
            resp, code = error_response('无效的置顶类型', code=400, status_code=400)
            return Response(resp, status=code)
        if pin_type == Post.PIN_GLOBAL:
            count = Post.objects.filter(pin_type=Post.PIN_GLOBAL, status=Post.STATUS_PUBLISHED).count()
            if count >= 3:
                resp, code = error_response('全局置顶数量已达上限（3篇）', code=400, status_code=400)
                return Response(resp, status=code)
        else:
            count = Post.objects.filter(pin_type=Post.PIN_SECTION, section_id=post.section_id, status=Post.STATUS_PUBLISHED).count()
            if count >= 5:
                resp, code = error_response('该板块置顶数量已达上限（5篇）', code=400, status_code=400)
                return Response(resp, status=code)
        post.pin(pin_type)
        return Response(success_response(message='置顶成功'))

    @action(detail=True, methods=['post'], url_path='unpin')
    def unpin(self, request, pk=None):
        """取消置顶（管理员）"""
        post = self.get_object()
        if not post:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)
        post.unpin()
        return Response(success_response(message='已取消置顶'))

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """编辑历史（管理员）"""
        post = self.get_object()
        if not post:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)
        histories = post.edit_history.all()
        serializer = PostEditHistorySerializer(histories, many=True)
        return Response(success_response(data=serializer.data))
