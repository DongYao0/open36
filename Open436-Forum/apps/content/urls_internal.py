"""
Content app internal API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_internal

router = DefaultRouter()
router.register(r'', views_internal.InternalPostViewSet, basename='internal-post')

urlpatterns = [
    path('', include(router.urls)),
]
