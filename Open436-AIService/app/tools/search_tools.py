"""
联网搜索工具 - 360 搜索（主）+ Bing/SearXNG/DuckDuckGo/Sogou（降级）
"""
import html as html_lib
import re
import logging
from langchain_core.tools import tool
from app.config import settings

logger = logging.getLogger(__name__)

# SearXNG 配置
SEARXNG_URL = settings.SEARXNG_URL.rstrip('/')
SEARCH_TIMEOUT_SECONDS = 8.0


def _plain_text(value: str) -> str:
    return re.sub(r'\s+', ' ', html_lib.unescape(re.sub(r'<[^>]+>', '', value))).strip()


async def _search_360(query: str, max_results: int = 5) -> list[dict]:
    """直连 360 搜索；目标 Linux 国内网络已验证可返回准确结果。"""
    import httpx

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                'https://www.so.com/s', params={'q': query},
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                       'AppleWebKit/537.36 Chrome/128.0 Safari/537.36'},
                timeout=SEARCH_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
        results = []
        for block in re.findall(r'<li class=["\']res-list["\'].*?</li>', resp.text, re.DOTALL):
            heading = re.search(r'<h3[^>]*>(.*?)</h3>', block, re.DOTALL)
            link = re.search(r'<a[^>]+data-mdurl="([^"]+)"[^>]*>(.*?)</a>',
                             heading.group(1) if heading else '', re.DOTALL)
            if not link:
                continue
            summary = re.search(r'<span class="res-list-summary">(.*?)</span>', block, re.DOTALL)
            title, url = _plain_text(link.group(2)), html_lib.unescape(link.group(1)).strip()
            excluded = re.search(r'(?:^|\.)(?:so\.com|360kan\.com)/', url)
            if title and url.startswith(('http://', 'https://')) and not excluded:
                results.append({'title': title, 'url': url,
                                'content': _plain_text(summary.group(1)) if summary else ''})
            if len(results) >= max_results:
                break
        if results:
            logger.info(f'360搜索成功: {len(results)} 条结果')
        return results
    except Exception as e:
        logger.warning(f'360搜索失败，降级到Bing: {e}')
        return []


async def _search_bing(query: str, max_results: int = 5) -> list[dict]:
    """直连 Bing HTML；目标 Linux 国内网络已验证可访问。"""
    import httpx

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                'https://cn.bing.com/search',
                params={'q': query, 'setlang': 'zh-cn'},
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 Chrome/128.0 Safari/537.36',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                },
                timeout=SEARCH_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
        results = []
        for block in re.findall(r'<li class="b_algo".*?</li>', resp.text, re.DOTALL):
            match = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if not match:
                continue
            snippet = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
            title = _plain_text(match.group(2))
            url = html_lib.unescape(match.group(1)).strip()
            if title and url.startswith(('http://', 'https://')):
                results.append({'title': title, 'url': url,
                                'content': _plain_text(snippet.group(1)) if snippet else ''})
            if len(results) >= max_results:
                break
        if results:
            logger.info(f'Bing搜索成功: {len(results)} 条结果')
        return results
    except Exception as e:
        logger.warning(f'Bing搜索失败，降级到SearXNG: {e}')
        return []


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
                timeout=SEARCH_TIMEOUT_SECONDS,
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
                timeout=SEARCH_TIMEOUT_SECONDS,
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
    搜索引擎优先级：360直连 → Bing直连 → SearXNG → DuckDuckGo → Sogou

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数，默认5
    """
    # 方案1: 目标 Linux 国内网络可稳定访问且结果相关的 360 HTML。
    results = await _search_360(query, max_results)
    if results:
        return results

    # 方案2: Bing HTML。
    results = await _search_bing(query, max_results)
    if results:
        return results

    # 方案3: SearXNG（聚合多引擎）
    results = await _search_searxng(query, max_results)
    if results:
        return results

    # 方案4: DuckDuckGo
    def _duckduckgo():
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            return [{'title': item.get('title', ''), 'url': item.get('href', ''),
                     'content': item.get('body', '')}
                    for item in ddgs.text(query, max_results=max_results)]

    try:
        import asyncio
        results = await asyncio.wait_for(asyncio.to_thread(_duckduckgo), timeout=SEARCH_TIMEOUT_SECONDS)
        if results:
            logger.info(f'DuckDuckGo搜索成功: {len(results)} 条结果')
            return results
    except Exception as e:
        logger.warning(f'DuckDuckGo搜索失败，切换到Sogou: {e}')

    # 方案5: Sogou（兜底）
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
            resp = await client.get(url, timeout=SEARCH_TIMEOUT_SECONDS, follow_redirects=True)
            resp.raise_for_status()
            text = re.sub(r'<[^>]+>', '', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:5000]
    except Exception as e:
        logger.error(f'抓取URL失败 {url}: {e}')
        return f'抓取失败: {str(e)}'
