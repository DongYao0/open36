"""
Content app public API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.PostViewSet, basename='post')

# 资源分享：复用 Post 模型，section=share；接入 /api/resources/
resource_router = DefaultRouter()
resource_router.register(r'', views.ResourceViewSet, basename='resource')

# /api/posts/ —— 帖子 CRUD
urlpatterns = [
    path('', include(router.urls)),
]

# /api/resources/ —— 资源分享视图（独立命名空间，避免与 posts 路由冲突）
urls_resource = [
    path('', include(resource_router.urls)),
]