"""
FastAPI依赖注入

安全模型（2026-09-07 加固）：
- 不再信任可伪造的 X-User-* 请求头
- 读取请求自身的 token 头 → 调 Auth 服务 /api/auth/verify 二次校验
- 校验结果缓存 60s，避免每个请求都打 Auth
"""
import time

import httpx
from fastapi import Header, HTTPException

from app.config import settings

# token → (user_info dict, expire_ts)
_TOKEN_CACHE = {}
_TOKEN_CACHE_TTL = 60
_TOKEN_CACHE_MAX = 5000


async def _verify_token(token: str) -> dict | None:
    """调用Auth服务校验token，返回用户信息或None"""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.post(
                f'{settings.AUTH_SERVICE_URL}/api/auth/verify',
                json={'token': token},
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
    except Exception:
        return None


async def _get_verified_user(token: str) -> dict | None:
    """带缓存的token校验"""
    now = time.time()
    cached = _TOKEN_CACHE.get(token)
    if cached and cached[1] > now:
        return cached[0]

    user_info = await _verify_token(token)
    if user_info:
        if len(_TOKEN_CACHE) >= _TOKEN_CACHE_MAX:
            for k in sorted(_TOKEN_CACHE, key=lambda k: _TOKEN_CACHE[k][1])[:_TOKEN_CACHE_MAX // 2]:
                _TOKEN_CACHE.pop(k, None)
        _TOKEN_CACHE[token] = (user_info, now + _TOKEN_CACHE_TTL)
    return user_info


def _extract_token(authorization: str | None, token_header: str | None) -> str:
    """从 Authorization: Bearer xxx 或 token: xxx 提取"""
    if authorization and authorization.startswith('Bearer '):
        return authorization[7:]
    return token_header or ''


async def get_current_user(
    authorization: str | None = Header(default=None),
    token: str | None = Header(default=None, alias='token'),
) -> dict:
    """校验token并返回当前登录用户信息（任意已登录用户）"""
    raw = _extract_token(authorization, token)
    if not raw:
        raise HTTPException(status_code=401, detail='未登录')
    user_info = await _get_verified_user(raw)
    if not user_info:
        raise HTTPException(status_code=401, detail='登录已失效')
    if user_info.get('status') != 'active':
        raise HTTPException(status_code=403, detail='账号已被禁用')
    return user_info


async def get_current_admin(
    authorization: str | None = Header(default=None),
    token: str | None = Header(default=None, alias='token'),
) -> int:
    """校验token并要求管理员角色，返回user_id"""
    user_info = await get_current_user(authorization, token)
    if user_info['role'] != 'admin':
        raise HTTPException(status_code=403, detail='权限不足：仅管理员可访问')
    return user_info['user_id']
