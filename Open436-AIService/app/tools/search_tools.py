"""
联网搜索工具 - Tavily Search API
"""
import logging
import httpx
from langchain_core.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)


@tool
async def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    联网搜索最新信息。适用于需要查找最新资讯、技术动态等时效性内容。

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数，默认5
    """
    if not settings.TAVILY_API_KEY:
        return [{'error': 'TAVILY_API_KEY未配置'}]

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(query=query, max_results=max_results)
        results = []
        for item in response.get('results', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': item.get('content', ''),
            })
        return results
    except Exception as e:
        logger.error(f'Tavily搜索失败: {e}')
        return [{'error': f'搜索失败: {str(e)}'}]


@tool
async def fetch_url(url: str) -> str:
    """
    抓取网页内容。提取纯文本返回。

    Args:
        url: 要抓取的网页URL
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0, follow_redirects=True)
            resp.raise_for_status()
            # 简单提取文本（去除HTML标签）
            import re
            text = re.sub(r'<[^>]+>', '', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:5000]  # 限制返回长度
    except Exception as e:
        logger.error(f'抓取URL失败 {url}: {e}')
        return f'抓取失败: {str(e)}'
