"""
Custom middleware for extracting user info with token verification.

安全模型（2026-09-07 加固）：
- 不再盲目信任 X-User-* 请求头（可被直连8003端口伪造）
- 读取请求自身携带的 token 头 → 调 Auth 服务 /api/auth/verify 二次校验
- 校验结果缓存 60s（token 为 key），避免每个请求都打 Auth
- 校验失败 = 匿名请求（request.is_authenticated = False）
- /internal/* 路径走独立的 InternalAPIKeyMiddleware（X-Internal-API-Key 校验）
"""
import logging
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# token → (user_info dict, expire_ts) 简单内存缓存
# 进程内缓存足够（单进程 runserver / gunicorn workers 各自独立）
_TOKEN_CACHE = {}
_TOKEN_CACHE_TTL = 60  # 秒
_TOKEN_CACHE_MAX = 5000  # 防内存膨胀


def _verify_token_with_auth(token):
    """调用 Auth 服务校验 token，返回 user_info dict 或 None"""
    try:
        resp = requests.post(
            f'{settings.AUTH_SERVICE_URL}/api/auth/verify',
            json={'token': token},
            timeout=3,
        )
        if resp.status_code != 200:
            return None
        body = resp.json()
        data = body.get('data') or {}
        if not data.get('valid'):
            return None
        user = data.get('data') or {}
        if not user.get('userId'):
            return None
        return {
            'user_id': int(user['userId']),
            'username': user.get('username', ''),
            'role': user.get('role', 'user'),
            'status': user.get('status', 'active'),
        }
    except Exception as e:
        logger.warning(f'Token verify failed (auth service unreachable?): {e}')
        return None


def _get_verified_user(token):
    """带缓存的 token 校验"""
    now = time.time()
    cached = _TOKEN_CACHE.get(token)
    if cached and cached[1] > now:
        return cached[0]

    user_info = _verify_token_with_auth(token)
    if user_info:
        # 简单淘汰：超限清空最旧一半
        if len(_TOKEN_CACHE) >= _TOKEN_CACHE_MAX:
            for k in sorted(_TOKEN_CACHE, key=lambda k: _TOKEN_CACHE[k][1])[:_TOKEN_CACHE_MAX // 2]:
                _TOKEN_CACHE.pop(k, None)
        _TOKEN_CACHE[token] = (user_info, now + _TOKEN_CACHE_TTL)
    return user_info


class UserInfoMiddleware:
    """基于 token 二次校验的用户识别中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id = None
        request.username = None
        request.user_role = None
        request.user_status = None
        request.is_authenticated = False
        request.is_admin = False

        # 内部 API 走独立 Key 校验，不在此处理用户身份
        if request.path.startswith('/internal/'):
            return self.get_response(request)

        token = request.META.get('HTTP_TOKEN') or ''
        if token.startswith('Bearer '):
            token = token[7:]

        if token:
            user_info = _get_verified_user(token)
            if user_info:
                request.user_id = user_info['user_id']
                request.username = user_info['username']
                request.user_role = user_info['role']
                request.user_status = user_info['status']
                request.is_authenticated = True
                request.is_admin = (user_info['role'] == 'admin')

        return self.get_response(request)


class InternalAPIKeyMiddleware:
    """校验 /internal/* 请求的 X-Internal-API-Key"""

    HEADER_NAME = 'HTTP_X_INTERNAL_API_KEY'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/internal/'):
            provided = request.META.get(self.HEADER_NAME, '')
            expected = settings.INTERNAL_API_KEY
            if not expected or provided != expected:
                from django.http import JsonResponse
                return JsonResponse(
                    {'code': 403, 'message': 'Invalid internal API key'},
                    status=403,
                )
        return self.get_response(request)
