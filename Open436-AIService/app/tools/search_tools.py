"""
联网搜索工具 - DuckDuckGo（免费，无需API Key）
"""
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
async def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    联网搜索最新信息。适用于需要查找最新资讯、技术动态等时效性内容。

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数，默认5
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = []
            for item in ddgs.text(query, max_results=max_results):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('href', ''),
                    'content': item.get('body', ''),
                })
            return results if results else [{'error': '未找到相关结果'}]
    except Exception as e:
        logger.error(f'DuckDuckGo搜索失败: {e}')
        return [{'error': f'搜索失败: {str(e)}'}]


@tool
async def fetch_url(url: str) -> str:
    """
    抓取网页内容。提取纯文本返回。

    Args:
        url: 要抓取的网页URL
    """
    try:
        import httpx
        import re

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0, follow_redirects=True)
            resp.raise_for_status()
            text = re.sub(r'<[^>]+>', '', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:5000]
    except Exception as e:
        logger.error(f'抓取URL失败 {url}: {e}')
        return f'抓取失败: {str(e)}'
