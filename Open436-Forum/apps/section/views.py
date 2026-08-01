"""
Section views
"""
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Sum

from .models import Section
from .serializers import (
    SectionListSerializer, SectionDetailSerializer, SectionCreateSerializer,
    SectionUpdateSerializer, SectionStatusSerializer, SectionReorderSerializer,
    SectionStatisticsSerializer,
)
from apps.core.permissions import IsAdminUser
from apps.core.responses import success_response, error_response


class SectionViewSet(viewsets.ModelViewSet):
    """板块视图集"""
    queryset = Section.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        if not getattr(self.request, 'is_admin', False):
            queryset = queryset.filter(is_enabled=True)
        return queryset.order_by('sort_order', 'id')

    def get_serializer_class(self):
        if self.action == 'list':
            return SectionListSerializer
        elif self.action == 'retrieve':
            return SectionDetailSerializer
        elif self.action == 'create':
            return SectionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SectionUpdateSerializer
        elif self.action == 'status':
            return SectionStatusSerializer
        elif self.action == 'reorder':
            return SectionReorderSerializer
        elif self.action == 'statistics':
            return SectionStatisticsSerializer
        return SectionDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def retrieve(self, request, *args, **kwargs):
        lookup_value = kwargs.get('pk')
        if lookup_value.isdigit():
            instance = get_object_or_404(Section, id=lookup_value)
        else:
            instance = get_object_or_404(Section, slug=lookup_value)
        if not getattr(request, 'is_admin', False) and not instance.is_enabled:
            return error_response(message='板块不存在', error='NotFound', status_code=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        detail_serializer = SectionDetailSerializer(instance)
        return success_response(data=detail_serializer.data, message='板块创建成功', status_code=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        detail_serializer = SectionDetailSerializer(instance)
        return success_response(data=detail_serializer.data, message='板块更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        can_delete, reason = instance.can_be_deleted()
        if not can_delete:
            return error_response(message=reason, error='CannotDelete', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            instance.disable()
            return success_response(message='板块已删除（禁用）')
        except ValueError as e:
            return error_response(message=str(e), error='CannotDelete', status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='status')
    def status(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_enabled = serializer.validated_data['is_enabled']
        try:
            if is_enabled:
                instance.enable()
                message = '板块已启用'
            else:
                instance.disable()
                message = '板块已禁用'
            detail_serializer = SectionDetailSerializer(instance)
            return success_response(data=detail_serializer.data, message=message)
        except ValueError as e:
            return error_response(message=str(e), error='OperationFailed', status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], url_path='reorder')
    def reorder(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sections_data = serializer.validated_data['sections']
        try:
            with transaction.atomic():
                for item in sections_data:
                    Section.objects.filter(id=item['id']).update(sort_order=item['sort_order'])
            return success_response(message=f'成功调整 {len(sections_data)} 个板块的排序')
        except Exception as e:
            return error_response(message=f'排序更新失败: {str(e)}', error='UpdateFailed', status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        total_sections = Section.objects.count()
        enabled_sections = Section.objects.filter(is_enabled=True).count()
        disabled_sections = total_sections - enabled_sections
        total_posts = Section.objects.aggregate(Sum('posts_count'))['posts_count__sum'] or 0
        sections = Section.objects.all().order_by('sort_order')
        sections_data = [{'id': s.id, 'slug': s.slug, 'name': s.name, 'is_enabled': s.is_enabled, 'posts_count': s.posts_count, 'sort_order': s.sort_order} for s in sections]
        return success_response(data={
            'total_sections': total_sections, 'enabled_sections': enabled_sections,
            'disabled_sections': disabled_sections, 'total_posts': total_posts,
            'sections': sections_data,
        })
