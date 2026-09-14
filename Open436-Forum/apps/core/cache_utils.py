"""
缓存访问统一入口（阶段4.1）

所有跨 Worker 共享缓存（Token 校验、用户资料）都经 safe_cache_*
 helpers：Redis 故障时记 warning 并按"未命中/跳过写入"降级，
 绝不让缓存异常打穿业务——论坛匿名浏览必须始终可用。
"""
import hashlib
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Redis 不可用时的降级结果标记（区分 None=未命中 与 None=故障）
CACHE_UNAVAILABLE = object()

_TOKEN_TTL = 60          # 有效 token 缓存 60s
_TOKEN_INVALID_TTL = 8   # 无效 token 负缓存 8s，防恶意刷 Auth
_PROFILE_TTL = 300       # 用户资料缓存 5 分钟
_PROFILE_MISS_TTL = 30   # 查无此人的用户短暂缓存 30s


def sha256_hex(value: str) -> str:
    """Token/键的摘要：缓存键不落原文（内存与 Redis 均如此）"""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def cache_get(key):
    """故障安全读取：Redis 异常返回 CACHE_UNAVAILABLE 而非抛出"""
    try:
        return cache.get(key)
    except Exception as e:  # django-redis 对连接错误抛 CommandError 等
        logger.warning('cache get failed (degrading): %s', e)
        return CACHE_UNAVAILABLE


def cache_set(key, value, ttl):
    """故障安全写入：失败仅记日志"""
    try:
        cache.set(key, value, ttl)
    except Exception as e:
        logger.warning('cache set failed (ignored): %s', e)


def cache_delete(key):
    try:
        cache.delete(key)
    except Exception as e:
        logger.warning('cache delete failed (ignored): %s', e)


# ── Token 校验缓存 ──

def token_key(token: str) -> str:
    return f'tok:{sha256_hex(token)}'


def get_token_user(token: str):
    """返回 (状态, user_info)；状态: 'hit'|'miss'|'invalid'|'unavailable'"""
    raw = cache_get(token_key(token))
    if raw is CACHE_UNAVAILABLE:
        return 'unavailable', None
    if raw is None:
        return 'miss', None
    if raw == {'invalid': True}:
        return 'invalid', None
    return 'hit', raw


def put_token_user(token: str, user_info: dict):
    cache_set(token_key(token), user_info, _TOKEN_TTL)


def put_token_invalid(token: str):
    cache_set(token_key(token), {'invalid': True}, _TOKEN_INVALID_TTL)


# ── 用户资料缓存（阶段4.2 批量作者信息）──

def profile_key(user_id) -> str:
    # v2 includes real_name; versioning avoids serving old nickname-only rows.
    return f'prof:v2:{user_id}'


def get_profiles(user_ids):
    """批量读取资料；返回 (hit: {id: profile}, miss: [id])"""
    if not user_ids:
        return {}, []
    keys = [profile_key(u) for u in user_ids]
    try:
        values = cache.get_many(keys)
    except Exception as e:
        logger.warning('cache get_many failed (degrading): %s', e)
        return {}, list(user_ids)
    hit, miss = {}, []
    for uid in user_ids:
        raw = values.get(profile_key(uid))
        if raw is None:
            miss.append(uid)
        elif raw != {'miss': True}:
            hit[uid] = raw
        # {'miss': True} = 查无此人，视为命中负缓存，不回源
    return hit, miss


def put_profiles(profiles: dict):
    """profiles: {user_id: profile_dict}"""
    if profiles:
        cache_set_many({profile_key(u): p for u, p in profiles.items()}, _PROFILE_TTL)


def put_profiles_miss(user_ids):
    if user_ids:
        cache_set_many({profile_key(u): {'miss': True} for u in user_ids}, _PROFILE_MISS_TTL)


def cache_set_many(mapping, ttl):
    try:
        cache.set_many(mapping, ttl)
    except Exception as e:
        logger.warning('cache set_many failed (ignored): %s', e)
