"""
Internal API views for service-to-service communication
"""
import logging
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.responses import success_response, error_response
from .models import Reply, PostLike, PostFavorite

logger = logging.getLogger(__name__)


class InternalReplyViewSet(viewsets.GenericViewSet):
    """内部回复视图集"""
    queryset = Reply.objects.all()

    @action(detail=True, methods=['get'], url_path='count')
    def count(self, request, pk=None):
        count = Reply.objects.filter(post_id=pk, is_deleted=False).count()
        return Response(success_response(data={'post_id': pk, 'replies_count': count}))

    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的用户ID', code=400, status_code=400)
            return Response(resp, status=code)
        queryset = Reply.objects.filter(author_id=user_id, is_deleted=False).order_by('-created_at')
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        replies = queryset[start:end]
        results = [{
            'reply_id': r.id,
            'content': r.content[:100] + ('...' if len(r.content) > 100 else ''),
            'post_id': r.post_id, 'post_title': None,
            'floor_number': r.floor_number, 'created_at': r.created_at,
        } for r in replies]
        return Response(success_response(data={
            'count': total,
            'next': f'/internal/comments/posts/by-user/{user_id}/?page={page + 1}' if end < total else None,
            'previous': f'/internal/comments/posts/by-user/{user_id}/?page={page - 1}' if page > 1 else None,
            'results': results,
        }))


class InternalInteractionViewSet(viewsets.GenericViewSet):
    """内部互动视图集"""

    @action(detail=True, methods=['get'], url_path='likes/count')
    def likes_count(self, request, pk=None):
        return Response(success_response(data={'post_id': pk, 'likes_count': PostLike.objects.filter(post_id=pk).count()}))

    @action(detail=True, methods=['get'], url_path='favorites/count')
    def favorites_count(self, request, pk=None):
        return Response(success_response(data={'post_id': pk, 'favorites_count': PostFavorite.objects.filter(post_id=pk).count()}))
