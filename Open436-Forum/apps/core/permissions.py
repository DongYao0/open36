"""
Custom permission classes
"""
from rest_framework import permissions


class IsAuthenticated(permissions.BasePermission):
    """需要登录"""
    message = '请先登录'

    def has_permission(self, request, view):
        return getattr(request, 'is_authenticated', False)


class IsAdminUser(permissions.BasePermission):
    """仅允许管理员"""
    message = '需要管理员权限'

    def has_permission(self, request, view):
        return getattr(request, 'is_admin', False)


class IsActiveUser(permissions.BasePermission):
    """仅允许状态为 active 的用户（排除 pending 和 disabled）"""
    message = '账号未审核通过，暂无法进行操作'

    def has_permission(self, request, view):
        status = getattr(request, 'user_status', None)
        return status == 'active'


class IsAuthorOrAdmin(permissions.BasePermission):
    """仅允许作者或管理员"""
    message = '只能操作自己的帖子'

    def has_object_permission(self, request, view, obj):
        if getattr(request, 'is_admin', False):
            return True
        return hasattr(obj, 'author_id') and obj.author_id == getattr(request, 'user_id', None)
