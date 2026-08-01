"""
Custom middleware for extracting user info from headers
"""
import logging

logger = logging.getLogger(__name__)


class UserInfoMiddleware:
    """从Kong Gateway注入的headers中提取用户信息"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.META.get('HTTP_X_USER_ID')
        username = request.META.get('HTTP_X_USERNAME')
        user_role = request.META.get('HTTP_X_USER_ROLE', 'user')
        user_status = request.META.get('HTTP_X_USER_STATUS')

        if user_id:
            try:
                request.user_id = int(user_id)
                request.username = username
                request.user_role = user_role
                request.user_status = user_status
                request.is_authenticated = True
                request.is_admin = (user_role == 'admin')
                logger.debug(f"User authenticated: {username} (ID: {user_id}, Role: {user_role}, Status: {user_status})")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid user_id in headers: {user_id}, Error: {e}")
                request.is_authenticated = False
                request.is_admin = False
        else:
            request.is_authenticated = False
            request.is_admin = False
            request.user_id = None
            request.username = None
            request.user_role = None
            request.user_status = None

        response = self.get_response(request)
        return response
