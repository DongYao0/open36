"""Resolve forum author profiles through AuthService with shared caching.

阶段4.2：帖子列表的作者信息不再每次请求都打 Auth——
  1) 先批量读共享缓存（生产 Redis，跨 Worker）；
  2) 只把缓存缺失的 user id 发给 Auth（单次批量请求，无串行逐个调用）；
  3) 命中资料缓存 5 分钟；查无此人负缓存 30 秒；
  4) Auth 调用失败：返回已有缓存命中部分，帖子列表照常渲染（昵称回退用户名）。
"""
import logging

import requests
from django.conf import settings

from apps.core import cache_utils

logger = logging.getLogger(__name__)


def _fetch_from_auth(user_ids):
    """调用 Auth 批量接口；返回 (profiles: {uid: profile}, error: bool)"""
    try:
        response = requests.post(
            f'{settings.AUTH_SERVICE_URL}/internal/users/batch',
            json={'userIds': list(user_ids)},
            headers={'X-Internal-API-Key': settings.INTERNAL_API_KEY},
            timeout=3,
        )
        response.raise_for_status()
        users = response.json().get('data', {}).get('users', [])
        profiles = {
            int(user['userId']): {
                'nickname': user.get('nickname'),
                'avatar_url': user.get('avatarUrl'),
            }
            for user in users
            if user.get('userId') is not None
        }
        return profiles, False
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        logger.warning('Resolve post authors failed: %s', exc)
        return {}, True


def get_author_profiles(posts):
    """Return profiles keyed by user id; profile lookup failure must not break posts."""
    user_ids = sorted({post.author_id for post in posts if not post.is_ai_generated})
    if not user_ids:
        return {}

    hit, missing = cache_utils.get_profiles(user_ids)

    if missing:
        fetched, errored = _fetch_from_auth(missing)
        hit.update(fetched)
        if not errored:
            found = set(fetched.keys())
            # Auth 正常返回但未包含的 id = 查无此人 → 负缓存 30s，防止
            # 已注销/幽灵作者在每个列表请求里反复回源。
            not_found = [uid for uid in missing if uid not in found]
            cache_utils.put_profiles(fetched)
            cache_utils.put_profiles_miss(not_found)
        # errored=True：Auth 故障，不写任何缓存，下个请求重试；
        # 此时返回已命中的部分（可能为空，serializer 回退显示用户名）。

    return hit
