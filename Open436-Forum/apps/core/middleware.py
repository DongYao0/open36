"""
Custom middleware for extracting user info with token verification.

安全模型（2026-09-07 加固，阶段4.1 并发改造）：
- 不再盲目信任 X-User-* 请求头（可被直连8003端口伪造）
- 读取请求自身携带的 token 头 → 调 Auth 服务 /api/auth/verify 二次校验
- 校验结果走共享缓存（生产 Redis，键为 token 的 SHA-256 摘要）：
  · 有效 token 缓存 60s，跨 Gunicorn Worker 复用，Auth QPS 降一个量级
  · 无效 token 负缓存 8s，恶意伪造不再逐请求穿透到 Auth
  · Auth 不可达/超时：不缓存结果，按匿名放行（浏览可用），
    写操作由各视图按 is_authenticated 明确拒绝
- /internal/* 路径走独立的 InternalAPIKeyMiddleware（X-Internal-API-Key 校验）
"""
import logging

import requests
from django.conf import settings

from apps.core import cache_utils

logger = logging.getLogger(__name__)

# Auth 不可达/超时标记：区别于"Auth 明确判定无效"，不参与负缓存
_AUTH_UNREACHABLE = object()


def _verify_token_with_auth(token):
    """调用 Auth 服务校验 token。
    返回 user_info dict / None（Auth 判定无效）/ _AUTH_UNREACHABLE（网络异常）"""
    try:
        resp = requests.post(
            f'{settings.AUTH_SERVICE_URL}/api/auth/verify',
            json={'token': token},
            timeout=3,
        )
    except Exception as e:
        logger.warning(f'Token verify failed (auth service unreachable?): {e}')
        return _AUTH_UNREACHABLE
    if resp.status_code != 200:
        return None
    try:
        body = resp.json()
    except Exception:
        return None
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


def _get_verified_user(token):
    """带共享缓存的 token 校验（Redis 键=SHA-256(token)，不落原文）"""
    state, cached = cache_utils.get_token_user(token)
    if state in ('hit', 'invalid'):
        return cached  # hit → user dict；invalid → None

    result = _verify_token_with_auth(token)
    if result is _AUTH_UNREACHABLE:
        # Auth 故障：不缓存任何结果，下一个请求重试（匿名放行）
        return None
    if result:
        cache_utils.put_token_user(token, result)
    else:
        # Auth 明确判定无效 → 负缓存 8s，挡住恶意伪造重放
        cache_utils.put_token_invalid(token)
    return result


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
