"""
联网搜索工具 - SearXNG（主）+ DuckDuckGo（备）+ Sogou（兜底）
"""
import re
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# SearXNG 配置
SEARXNG_URL = 'http://localhost:8888'


async def _search_searxng(query: str, max_results: int = 5) -> list[dict]:
    """SearXNG 元搜索引擎（主方案）- 聚合 Google/Bing/DuckDuckGo 等"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'{SEARXNG_URL}/search',
                params={
                    'q': query,
                    'format': 'json',
                    'language': 'auto',
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get('results', [])[:max_results]:
                title = item.get('title', '')
                url = item.get('url', '')
                content = item.get('content', '')
                engines = item.get('engines', [])
                score = item.get('score', 0)

                if title and url:
                    results.append({
                        'title': title,
                        'url': url,
                        'content': content,
                        'engines': engines,
                        'score': score,
                    })

            if results:
                logger.info(f'SearXNG搜索成功: {len(results)} 条结果 (engines: {set(e for r in results for e in r.get("engines", []))})')
                return results
            else:
                logger.warning('SearXNG无结果，降级到DuckDuckGo')
                return []
    except Exception as e:
        logger.warning(f'SearXNG搜索失败，降级到DuckDuckGo: {e}')
        return []


async def _search_sogou(query: str, max_results: int = 5) -> list[dict]:
    """Sogou搜索引擎（兜底方案）"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                'https://www.sogou.com/web',
                params={'query': query},
                timeout=15.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                },
            )
            resp.raise_for_status()
            html = resp.text

            results = []
            pattern = r'<h3[^>]*>.*?<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html, re.DOTALL)

            for url, title in matches[:max_results]:
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                if url.startswith('/link?url='):
                    url = f'https://www.sogou.com{url}'
                if clean_title and url:
                    results.append({
                        'title': clean_title,
                        'url': url,
                        'content': '',
                    })

            return results if results else [{'error': 'Sogou未找到结果'}]
    except Exception as e:
        logger.error(f'Sogou搜索失败: {e}')
        return [{'error': f'Sogou搜索失败: {str(e)}'}]


@tool
async def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    联网搜索最新信息。适用于需要查找最新资讯、技术动态等时效性内容。
    搜索引擎优先级：SearXNG（聚合Google/Bing）→ DuckDuckGo → Sogou

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数，默认5
    """
    # 方案1: SearXNG（聚合多引擎，结果最新）
    results = await _search_searxng(query, max_results)
    if results:
        return results

    # 方案2: DuckDuckGo
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
            if results:
                logger.info(f'DuckDuckGo搜索成功: {len(results)} 条结果')
                return results
    except Exception as e:
        logger.warning(f'DuckDuckGo搜索失败，切换到Sogou: {e}')

    # 方案3: Sogou（兜底）
    logger.info(f'使用Sogou搜索引擎: {query}')
    return await _search_sogou(query, max_results)


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
