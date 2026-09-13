"""
/api/resources/ 路由 —— 接入 ResourceViewSet（复用 Post 模型，section='share'）
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

resource_router = DefaultRouter()
resource_router.register(r'', views.ResourceViewSet, basename='resource')

urlpatterns = [
    path('', include(resource_router.urls)),
]