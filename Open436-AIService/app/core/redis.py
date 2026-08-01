"""
Redis连接管理
"""
import redis.asyncio as aioredis

from app.config import settings

redis_client: aioredis.Redis = None


async def init_redis():
    """初始化Redis连接"""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis():
    """关闭Redis连接"""
    global redis_client
    if redis_client:
        await redis_client.close()


def get_redis() -> aioredis.Redis:
    """获取Redis客户端"""
    return redis_client
