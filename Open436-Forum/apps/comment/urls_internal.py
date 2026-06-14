"""
Comment app internal API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_internal

router = DefaultRouter()
router.register(r'posts', views_internal.InternalReplyViewSet, basename='internal-post-replies')
router.register(r'posts', views_internal.InternalInteractionViewSet, basename='internal-post-interactions')

urlpatterns = [
    path('', include(router.urls)),
]
