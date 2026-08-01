"""
爬虫工具 - 调用 CrawlerService API 收集数据
Router Agent 通过这些工具获取原始数据，再分发给下游 Agent 处理

P0优化：
1. URL级缓存（TTL 1h）—— 相同URL/关键词二次请求几乎0耗时
2. 失败不缓存，避免缓存脏数据
"""
import hashlib
import json
import logging
from langchain_core.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)

CRAWLER_URL = settings.CRAWLER_SERVICE_URL

# 缓存TTL（秒）
URL_CACHE_TTL = 3600        # 单页爬取结果：1小时（页面内容相对稳定）
SEARCH_CACHE_TTL = 900      # 搜索结果：15分钟（搜索结果变动较快，TTL短）


async def _cache_get(key: str):
    """从Redis读缓存，未命中或异常返回None"""
    try:
        from app.core.redis import get_redis
        redis = get_redis()
        if redis is None:
            return None
        cached = await redis.get(key)
        if cached:
            logger.info(f'缓存命中: {key[:40]}')
            return json.loads(cached)
    except Exception as e:
        logger.warning(f'读缓存异常(忽略): {e}')
    return None


async def _cache_set(key: str, value, ttl: int):
    """写缓存，仅缓存成功结果，异常忽略"""
    if not isinstance(value, dict) or not value.get('success', True):
        logger.info(f'跳过缓存(失败结果): {key[:40]}')
        return  # 失败结果不缓存
    try:
        from app.core.redis import get_redis
        redis = get_redis()
        if redis is None:
            logger.warning('redis_client为None，跳过缓存写入')
            return
        await redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        logger.info(f'缓存已写入: {key[:40]} TTL={ttl}s')
    except Exception as e:
        logger.warning(f'写缓存异常(忽略): {e}')


def _cache_key(*parts) -> str:
    """生成缓存key：crawl:md5(组合参数)"""
    raw = '|'.join(str(p) for p in parts)
    return f'crawl:{hashlib.md5(raw.encode("utf-8")).hexdigest()}'


@tool
async def crawl_webpage(url: str) -> dict:
    """
    爬取单个网页，返回 Markdown 内容、标题、元数据。
    适用于需要获取指定网页的完整内容。

    Args:
        url: 要爬取的网页 URL
    """
    import httpx

    # P0: URL级缓存
    cache_key = _cache_key('url', url)
    cached = await _cache_get(cache_key)
    if cached is not None:
        cached['_cached'] = True
        return cached

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{CRAWLER_URL}/crawl/single',
                json={'url': url},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            result = {
                'success': data.get('success', False),
                'url': data.get('url', ''),
                'title': data.get('title', ''),
                'markdown': data.get('markdown', ''),
                'word_count': data.get('word_count', 0),
            }
            await _cache_set(cache_key, result, URL_CACHE_TTL)
            return result
    except Exception as e:
        logger.error(f'爬取网页失败 {url}: {e}')
        return {'success': False, 'error': str(e)}


@tool
async def crawl_search(keyword: str, max_results: int = 5, engine: str = 'sogou') -> dict:
    """
    搜索关键词并爬取搜索结果页面。返回多个页面的标题、URL、Markdown 内容。
    适用于需要搜索某个主题的相关资料。

    Args:
        keyword: 搜索关键词
        max_results: 最大结果数，默认5，最大20
        engine: 搜索引擎，可选 sogou/bing/baidu/google，默认 sogou
    """
    import httpx

    # P0: 关键词级缓存（TTL较短，搜索结果变动快）
    cache_key = _cache_key('search', keyword, max_results, engine)
    cached = await _cache_get(cache_key)
    if cached is not None:
        cached['_cached'] = True
        return cached

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{CRAWLER_URL}/crawl/search',
                json={
                    'keyword': keyword,
                    'max_results': min(max_results, 20),
                    'engine': engine,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()

            pages = []
            for p in data.get('pages', []):
                if p.get('success'):
                    pages.append({
                        'url': p.get('url', ''),
                        'title': p.get('title', ''),
                        'markdown': p.get('markdown', ''),
                        'word_count': p.get('word_count', 0),
                    })

            result = {
                'success': data.get('success', False),
                'keyword': data.get('keyword', keyword),
                'total_pages': data.get('total_pages', 0),
                'pages': pages,
            }
            await _cache_set(cache_key, result, SEARCH_CACHE_TTL)
            return result
    except Exception as e:
        logger.error(f'搜索爬取失败 "{keyword}": {e}')
        return {'success': False, 'error': str(e)}


@tool
async def crawl_deep(url: str, max_depth: int = 1, max_pages: int = 5) -> dict:
    """
    深度爬取同域页面。从起始 URL 出发，BFS 遍历同域链接。
    适用于需要爬取某个网站的多个页面（如文档站、教程站）。

    Args:
        url: 起始 URL
        max_depth: 最大爬取深度，默认1，最大3
        max_pages: 最大页面数，默认5，最大20
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{CRAWLER_URL}/crawl/deep',
                json={
                    'url': url,
                    'max_depth': min(max_depth, 3),
                    'max_pages': min(max_pages, 20),
                },
                timeout=180.0,
            )
            resp.raise_for_status()
            data = resp.json()

            pages = []
            for p in data.get('pages', []):
                if p.get('success'):
                    pages.append({
                        'url': p.get('url', ''),
                        'title': p.get('title', ''),
                        'markdown': (p.get('markdown') or '')[:3000],
                        'word_count': p.get('word_count', 0),
                    })

            return {
                'success': data.get('success', False),
                'total_pages': data.get('total_pages', 0),
                'pages': pages,
            }
    except Exception as e:
        logger.error(f'深度爬取失败 {url}: {e}')
        return {'success': False, 'error': str(e)}
