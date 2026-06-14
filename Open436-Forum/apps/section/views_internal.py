"""
Internal views for inter-service communication
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Section
from apps.core.responses import success_response, error_response


class InternalSectionViewSet(viewsets.ViewSet):
    """内部板块视图集"""
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'], url_path='increment-posts')
    def increment_posts(self, request, pk=None):
        section = get_object_or_404(Section, id=pk)
        value = request.data.get('value', 1)
        try:
            value = int(value)
        except (ValueError, TypeError):
            return error_response(message='value 必须是整数', error='InvalidParameter', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            section.increment_posts_count(value)
            return success_response(data={'id': section.id, 'slug': section.slug, 'posts_count': section.posts_count}, message='帖子数量已更新')
        except Exception as e:
            return error_response(message=f'更新失败: {str(e)}', error='UpdateFailed', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='validate')
    def validate(self, request, pk=None):
        try:
            section = Section.objects.get(id=pk, is_enabled=True)
            return success_response(data={'id': section.id, 'slug': section.slug, 'name': section.name, 'is_enabled': section.is_enabled}, message='板块有效')
        except Section.DoesNotExist:
            return error_response(message='板块不存在或已禁用', error='SectionNotFound', status_code=status.HTTP_404_NOT_FOUND)

    def list(self, request):
        sections = Section.get_enabled_sections()
        results = [{'id': s.id, 'slug': s.slug, 'name': s.name, 'description': s.description, 'is_enabled': s.is_enabled} for s in sections]
        return success_response(data={'sections': results})
