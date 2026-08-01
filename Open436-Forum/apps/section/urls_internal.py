"""
Section internal API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_internal import InternalSectionViewSet

router = DefaultRouter()
router.register(r'', InternalSectionViewSet, basename='internal-section')

urlpatterns = [
    path('', include(router.urls)),
]
