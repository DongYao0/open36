"""
AI 流式任务全局并发限制（阶段7，压测前置加固）

跨进程（多 Uvicorn worker）共享的 Redis 计数信号量。压测修复要点：
  1. 只有成功取得活跃槽位才会释放（acquired 标志；fail-open 降级路径
     从未递增计数，释放时也绝不递减）；
  2. 释放用 Lua 原子">0 才减"，任何路径都不会把计数减成负数；
  3. 活跃槽 TTL = max(900, 流超时×2+300)：生产 AI_STREAM_TIMEOUT_SECONDS=300
     → TTL=900s，明显大于最长流任务，崩溃残留最多 15 分钟自愈；
  4. 队列满 → 429 + Retry-After；等待本身有 30s 上限；
  5. Redis 故障 fail-open（可用性优先），计数不参与降级路径。
"""
import asyncio
import logging

from app.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

ACTIVE_KEY = 'ai:stream:active'
WAITING_KEY = 'ai:stream:waiting'

# 槽位自愈 TTL：必须明显大于最长流任务（生产 300s 超时）
KEY_TTL_SECONDS = max(900, settings.AI_STREAM_TIMEOUT_SECONDS * 2 + 300)

# 原子释放：仅当计数 >0 时递减，防止任何路径把计数减成负数
_RELEASE_LUA = """
local v = redis.call('GET', KEYS[1])
if v and tonumber(v) > 0 then
    return redis.call('DECR', KEYS[1])
end
return -1
"""


class StreamBusyError(Exception):
    """队列已满：应返回 429 + Retry-After"""

    def __init__(self, retry_after: int = 5):
        self.retry_after = retry_after
        super().__init__('AI 服务繁忙，请稍后重试')


async def _try_acquire_active() -> bool:
    redis = get_redis()
    active = await redis.incr(ACTIVE_KEY)
    if active == 1:
        await redis.expire(ACTIVE_KEY, KEY_TTL_SECONDS)
    if active > settings.AI_STREAM_MAX_CONCURRENT:
        await _safe_release(ACTIVE_KEY)
        return False
    return True


async def _safe_release(key: str) -> None:
    """原子释放（>0 才减）；异常仅记日志，绝不抛出"""
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.eval(_RELEASE_LUA, 1, key)
    except Exception as e:  # noqa: BLE001
        logger.warning('release %s failed (ignored): %s', key, e)


class GlobalStreamSlot:
    """async with 语义的全局流任务槽位（压测加固版）"""

    def __init__(self):
        self._acquired = False   # 只有真正递增过 ACTIVE_KEY 才允许释放
        self._redis_ok = False   # 降级（fail-open）路径未占用计数

    async def __aenter__(self):
        redis = get_redis()
        if redis is None:
            self._redis_ok = False  # 单测/Redis 未初始化：放行，不占计数
            return self
        try:
            waiting = await redis.incr(WAITING_KEY)
            if waiting == 1:
                await redis.expire(WAITING_KEY, KEY_TTL_SECONDS)
            if waiting > settings.AI_STREAM_QUEUE_SIZE:
                await _safe_release(WAITING_KEY)
                raise StreamBusyError(retry_after=5)
            try:
                deadline = asyncio.get_event_loop().time() + 30.0
                while not await _try_acquire_active():
                    if asyncio.get_event_loop().time() > deadline:
                        raise StreamBusyError(retry_after=10)
                    await asyncio.sleep(0.5)
                self._acquired = True   # 已取得活跃槽：此后释放才合法
                self._redis_ok = True
            finally:
                await _safe_release(WAITING_KEY)
            return self
        except StreamBusyError:
            raise
        except Exception as e:  # Redis 故障：fail-open，不占计数
            self._redis_ok = False
            self._acquired = False
            logger.warning('stream limiter degraded (fail-open): %s', e)
            return self

    async def __aexit__(self, exc_type, exc, tb):
        # 只有成功取得过活跃槽位才释放；降级路径绝不递减
        if self._acquired and self._redis_ok:
            await _safe_release(ACTIVE_KEY)
        self._acquired = False
        return False
