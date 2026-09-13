"""
AI 流式任务全局并发限制（阶段7）

跨进程（多 Uvicorn worker）共享的 Redis 计数信号量：
  - 全局同时执行的 LLM 流任务上限 AI_STREAM_MAX_CONCURRENT（默认 20）；
  - 等待队列上限 AI_STREAM_QUEUE_SIZE（默认 50），队满返回 429 + Retry-After；
  - 计数键带 TTL：进程崩溃未释放的槽位在 TTL 后自愈；
  - 客户端断开（浏览器关页）→ 生成器收到 CancelledError → finally 释放槽位，
    下游 LLM 任务的取消由 chat_service 原有 stop 机制配合完成；
  - Redis 故障时放行（fail-open）：AI 可用性优先于精确限流，
    单进程内仍有 asyncio.Semaphore 兜底（chat_service 原有逻辑）。
"""
import logging

from app.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

ACTIVE_KEY = 'ai:stream:active'
WAITING_KEY = 'ai:stream:waiting'
# 槽位自愈 TTL：远大于最长流任务（90s 超时），崩溃残留最多阻塞 5 分钟
KEY_TTL_SECONDS = 300


class StreamBusyError(Exception):
    """队列已满：应返回 429 + Retry-After"""

    def __init__(self, retry_after: int = 5):
        self.retry_after = retry_after
        super().__init__('AI 服务繁忙，请稍后重试')


async def _try_acquire_active() -> bool:
    redis = get_redis()
    if redis is None:
        return True  # Redis 未初始化（单测/降级）：放行
    active = await redis.incr(ACTIVE_KEY)
    if active == 1:
        await redis.expire(ACTIVE_KEY, KEY_TTL_SECONDS)
    if active > settings.AI_STREAM_MAX_CONCURRENT:
        await redis.decr(ACTIVE_KEY)
        return False
    return True


class GlobalStreamSlot:
    """async with 语义的全局流任务槽位"""

    async def __aenter__(self):
        redis = get_redis()
        if redis is None:
            return self
        try:
            waiting = await redis.incr(WAITING_KEY)
            if waiting == 1:
                await redis.expire(WAITING_KEY, KEY_TTL_SECONDS)
            if waiting > settings.AI_STREAM_QUEUE_SIZE:
                await redis.decr(WAITING_KEY)
                raise StreamBusyError(retry_after=5)
            try:
                import asyncio
                deadline = asyncio.get_event_loop().time() + 30.0
                while not await _try_acquire_active():
                    if asyncio.get_event_loop().time() > deadline:
                        raise StreamBusyError(retry_after=10)
                    await asyncio.sleep(0.5)
            finally:
                await redis.decr(WAITING_KEY)
            return self
        except StreamBusyError:
            raise
        except Exception as e:  # Redis 故障：fail-open
            logger.warning('stream limiter degraded (fail-open): %s', e)
            return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            redis = get_redis()
            if redis is not None:
                await redis.decr(ACTIVE_KEY)
        except Exception as e:
            logger.warning('release stream slot failed: %s', e)
        return False
