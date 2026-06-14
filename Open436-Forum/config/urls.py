"""
URL configuration for Open436 Forum Service.
合并 Content + Comment + Section，保持所有原有 API 路径不变。
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── 公开 API（保持原有路径） ──
    # ContentService: /api/posts/
    path('api/posts/', include('apps.content.urls')),
    # CommentService: /api/comments/ → 内部路由到 comment app
    path('api/comments/', include('apps.comment.urls_comment')),
    # SectionService: /api/sections/
    path('api/sections/', include('apps.section.urls')),
    # CommentService 的非 comments 前缀路径: /api/replies/, /api/favorites/, /api/topics/, /api/follows/
    path('api/', include('apps.comment.urls_root')),

    # ── 内部 API ──
    path('internal/posts/', include('apps.content.urls_internal')),
    path('internal/comments/', include('apps.comment.urls_internal')),
    path('internal/sections/', include('apps.section.urls_internal')),

    # ── 健康检查 ──
    path('', include('apps.core.urls')),
]
