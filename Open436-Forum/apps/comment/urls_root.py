"""
Comment app URLs — 挂载在 /api/ 下
保持原有路径: /api/replies/, /api/topics/, /api/favorites/, /api/follows/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'replies', views.ReplyViewSet, basename='reply')
router.register(r'topics', views.TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
]
