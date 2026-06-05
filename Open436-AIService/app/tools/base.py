"""
工具基类 - 统一的内部API调用封装
"""
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def call_internal(service_url: str, method: str, path: str,
                        headers_extra: dict = None, **kwargs) -> dict:
    """
    调用内部API的统一封装

    Args:
        service_url: 服务基础URL
        method: HTTP方法
        path: API路径
        headers_extra: 额外请求头
        **kwargs: 传递给httpx的其他参数

    Returns:
        API响应的JSON数据
    """
    headers = {'X-Internal-API-Key': settings.INTERNAL_API_KEY}
    if headers_extra:
        headers.update(headers_extra)

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=method,
            url=f'{service_url}{path}',
            headers=headers,
            timeout=30.0,
            **kwargs,
        )
        resp.raise_for_status()
        return resp.json()
