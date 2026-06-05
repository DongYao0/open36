"""
论坛相关工具 - 封装M3/M5内部API
"""
from langchain_core.tools import tool

from app.config import settings
from app.tools.base import call_internal


@tool
async def list_sections() -> dict:
    """获取所有启用的板块列表。返回板块的id、name、description等信息。"""
    result = await call_internal(
        settings.SECTION_SERVICE_URL, 'GET', '/internal/sections/'
    )
    return result


@tool
async def create_post(title: str, content: str, section_id: int, author_id: int) -> dict:
    """
    创建论坛帖子。

    Args:
        title: 帖子标题，5-100字符
        content: 帖子内容，Markdown格式，10-50000字符
        section_id: 板块ID
        author_id: 作者用户ID
    """
    result = await call_internal(
        settings.CONTENT_SERVICE_URL, 'POST', '/internal/posts/',
        json={
            'title': title,
            'content': content,
            'section_id': section_id,
            'author_id': author_id,
        },
    )
    return result


@tool
async def list_posts(section_id: int = None, page: int = 1, page_size: int = 20) -> dict:
    """
    查询帖子列表。

    Args:
        section_id: 板块ID（可选，不传则查全部）
        page: 页码，默认1
        page_size: 每页数量，默认20
    """
    params = {'page': page, 'page_size': page_size}
    if section_id:
        params['section_id'] = section_id

    result = await call_internal(
        settings.CONTENT_SERVICE_URL, 'GET', '/internal/posts/list/',
        params=params,
    )
    return result


@tool
async def update_post(post_id: int, title: str = None, content: str = None, author_id: int = 0) -> dict:
    """
    编辑论坛帖子。

    Args:
        post_id: 帖子ID
        title: 新标题（可选）
        content: 新内容（可选）
        author_id: 编辑者用户ID
    """
    data = {'author_id': author_id}
    if title:
        data['title'] = title
    if content:
        data['content'] = content

    result = await call_internal(
        settings.CONTENT_SERVICE_URL, 'PUT', f'/internal/posts/{post_id}/',
        json=data,
    )
    return result
