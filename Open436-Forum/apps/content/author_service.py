"""Resolve forum author profiles through AuthService in one bounded request."""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_author_profiles(posts):
    """Return profiles keyed by user id; profile lookup failure must not break posts."""
    user_ids = sorted({post.author_id for post in posts if not post.is_ai_generated})
    if not user_ids:
        return {}

    try:
        response = requests.post(
            f'{settings.AUTH_SERVICE_URL}/internal/users/batch',
            json={'userIds': user_ids},
            headers={'X-Internal-API-Key': settings.INTERNAL_API_KEY},
            timeout=3,
        )
        response.raise_for_status()
        users = response.json().get('data', {}).get('users', [])
        return {
            int(user['userId']): {
                'nickname': user.get('nickname'),
                'avatar_url': user.get('avatarUrl'),
            }
            for user in users
            if user.get('userId') is not None
        }
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        logger.warning('Resolve post authors failed: %s', exc)
        return {}
