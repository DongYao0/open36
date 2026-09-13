"""论坛草稿工作流：草稿可反复修改，明确发布才写入论坛。"""
import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_chat_model
from app.tools.forum_tools import create_post, list_sections
from app.tools.search_tools import search_web

logger = logging.getLogger(__name__)
_DRAFT_MARKER = re.compile(r'<!--open436-forum-draft:(.*?)-->', re.DOTALL)
_EDIT_WORDS = re.compile(r'(改|修改|调整|润色|扩展|添加|删除|减少|增加|缩短|重写|标题|摘要|正文|段落|条)')
_SEARCH_WORDS = re.compile(r'(搜索|搜集|查找|查阅|联网|最新|资料|参考|调研|search)', re.IGNORECASE)
_WORKFLOW_STATUS = re.compile(r'(?:草稿|暂不发布|先不发布|尚未发布|待确认)')

_SYSTEM = """你是 Open436 论坛写作助手。返回且只返回一个 JSON 对象：
{"post_type":"tech|resource","title":"...","summary":"...","content":"...","resource_url":"..."}
字段均表示当前完整帖子。技术帖 resource_url 必须为空；资源帖必须给出用户提供或可信的直接资源链接。
标题5-100字，摘要20-300字，正文清晰、有实质内容。用户是在制作草稿：除非系统明确说“现在发布”，绝对不能声称已经发布。
标题、摘要和正文只能包含帖子本身，不得写入“草稿”“暂不发布”“待确认”等工作流状态。"""


def _clean_workflow_status(text: str) -> str:
    """移除模型偶尔写进正文的草稿流程说明，发布时不再污染帖子内容。"""
    parts = re.split(r'(?<=[。！？!?])', text)
    return ''.join(part for part in parts if not _WORKFLOW_STATUS.search(part)).strip()


def _load_draft(history: list[dict]) -> dict | None:
    for item in reversed(history or []):
        if item.get('role') != 'assistant':
            continue
        match = _DRAFT_MARKER.search(item.get('content', ''))
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.warning('论坛草稿标记无法解析')
    return None


def has_forum_draft(history: list[dict]) -> bool:
    return _load_draft(history) is not None


def _should_publish(message: str) -> bool:
    """仅接受明确的发布命令，避免把“修改发布信息”误当作发布。"""
    if _EDIT_WORDS.search(message):
        return False
    return bool(re.search(r'(?:^|(?:现在|确认|请|帮我|直接|把这篇|将这篇))\s*'
                          r'(?:上传|发布|发帖|提交)\s*(?:这篇|当前|该)?\s*'
                          r'(?:帖子|文章|技术(?:交流)?(?:帖|帖子|贴)|资源(?:分享)?(?:帖|帖子|贴))?\s*(?:吧|呀|。|！|!|$)', message))


def is_draft_followup(message: str, history: list[dict]) -> bool:
    return has_forum_draft(history) and (_should_publish(message) or bool(_EDIT_WORDS.search(message)))


def is_forum_request(message: str) -> bool:
    """无需依赖模型的首轮论坛意图识别，避免草稿被误分到闲聊。"""
    return bool(re.search(r'(技术(?:交流)?帖|资源(?:分享)?帖|论坛.{0,8}(?:写|改|生成|发布)|'
                          r'(?:写|生成|创建|修改|润色).{0,12}(?:技术|资源|帖子|文章))', message))


def _parse_draft(raw: str, fallback: dict | None) -> dict:
    text = raw.strip()
    if '```' in text:
        text = re.sub(r'```(?:json)?\s*', '', text).replace('```', '').strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    try:
        value = json.loads(match.group() if match else text)
    except (json.JSONDecodeError, AttributeError):
        if fallback:
            return fallback
        raise ValueError('AI 未返回可用的帖子草稿')
    post_type = value.get('post_type', fallback.get('post_type') if fallback else 'tech')
    if post_type not in {'tech', 'resource'}:
        post_type = 'tech'
    draft = {
        'post_type': post_type,
        'title': str(value.get('title', '')).strip(),
        'summary': _clean_workflow_status(str(value.get('summary', '')).strip()),
        'content': _clean_workflow_status(str(value.get('content', '')).strip()),
        'resource_url': str(value.get('resource_url', '') or '').strip(),
        'sources': value.get('sources', fallback.get('sources', []) if fallback else []),
    }
    if post_type == 'tech':
        draft['resource_url'] = ''
    if len(draft['title']) < 5 or len(draft['summary']) < 20 or len(draft['content']) < 10:
        raise ValueError('AI 生成的标题、摘要或正文不完整')
    return draft


def _valid_search_results(results) -> list[dict]:
    if not isinstance(results, list):
        return []
    return [
        {'title': str(item.get('title', '')).strip(),
         'url': str(item.get('url', '')).strip(),
         'content': str(item.get('content', '')).strip()}
        for item in results
        if isinstance(item, dict) and item.get('title') and item.get('url')
    ]


def _search_query(message: str) -> str:
    """从“搜索 X，再生成/发布 Y”式指令中提取 X，避免控制语污染检索结果。"""
    match = re.search(
        r'(?:搜索|搜集|查找|查阅|调研)\s*(.+?)'
        r'(?=[，,。；;]\s*(?:再|然后|并|并且|并写|生成|创建|写|整理|发布|发帖)|$)',
        message,
        re.IGNORECASE,
    )
    query = match.group(1) if match else message
    query = re.sub(r'【[^】]*(?:测试|验收)[^】]*】', ' ', query)
    query = re.sub(r'^\s*(?:请|帮我|麻烦)?\s*(?:先|再)?\s*(?:联网)?\s*', '', query)
    query = re.sub(r'\s+', ' ', query).strip(' ，,。；;：:')
    return (query or message.strip())[:200]


def _attach_sources(draft: dict, sources: list[dict]) -> dict:
    draft['sources'] = [{'title': item['title'], 'url': item['url']} for item in sources]
    if sources:
        links = '\n'.join(f"- [{item['title']}]({item['url']})" for item in sources)
        draft['content'] = f"{draft['content'].rstrip()}\n\n## 参考来源\n\n{links}"
    return draft


async def _generate(message: str, history: list[dict], draft: dict | None,
                    sources: list[dict] | None = None) -> dict:
    context = json.dumps(draft, ensure_ascii=False) if draft else '无，需根据用户请求新建。'
    source_context = '\n\n'.join(
        f"来源：{item['title']}\nURL：{item['url']}\n摘要：{item.get('content', '')[:1200]}"
        for item in (sources or [])
    ) or '本轮没有外部搜索资料。'
    prompt = f"""当前草稿：{context}

用户本轮要求：{message}

实时搜索资料：
{source_context}

请输出修改后的完整 JSON。若提供了搜索资料，正文事实必须以资料为依据，不得编造，
但不要在正文中自行增加参考来源章节（系统会统一追加）。若用户仅要求修改某一处，
其余字段必须保留；“那/它/这篇/减少到5条”等指代均指当前草稿。"""
    model = get_chat_model(temperature=0.5, max_tokens=4096)
    answer = await model.ainvoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    return _parse_draft(answer.content or '', draft)


async def _section_id(post_type: str) -> int:
    result = await list_sections.ainvoke({})
    values = result.get('results') or result.get('data') or result.get('items') or []
    keywords = ('资源', '分享') if post_type == 'resource' else ('技术', '交流')
    for section in values:
        name = str(section.get('name', ''))
        if any(keyword in name for keyword in keywords):
            return int(section['id'])
    raise ValueError('未找到对应论坛板块，请先在论坛创建技术交流或资源分享板块')


def _display_draft(draft: dict, published: bool = False) -> str:
    kind = '资源分享' if draft['post_type'] == 'resource' else '技术交流'
    state = '已发布' if published else '草稿已更新；确认无误后请明确说“上传帖子”或“发布帖子”。'
    resource = f"\n资源链接：{draft['resource_url']}" if draft['resource_url'] else ''
    marker = json.dumps(draft, ensure_ascii=False, separators=(',', ':'))
    return (f"{kind}{'已发布' if published else '草稿'}\n\n"
            f"标题：{draft['title']}\n\n摘要：{draft['summary']}\n\n{draft['content']}{resource}\n\n{state}"
            f"<!--open436-forum-draft:{marker}-->")


async def run_forum_draft(message: str, user_id: int, history: list[dict]) -> dict:
    """生成或修改草稿；只有明确发布词才调用内部发帖接口。"""
    previous = _load_draft(history)
    publish = _should_publish(message)
    tool_calls: list[dict] = []

    # 发布必须使用用户确认过的草稿，不能再让模型暗中改写一次。
    if publish and previous:
        draft = previous
    else:
        sources = previous.get('sources', []) if previous else []
        if not previous and _SEARCH_WORDS.search(message):
            query = _search_query(message)
            results = await search_web.ainvoke({'query': query, 'max_results': 5})
            sources = _valid_search_results(results)
            status = 'success' if sources else 'failed'
            tool_calls.append({
                'tool_name': 'search_web', 'status': status,
                'tool_args': {'query': query, 'max_results': 5},
                'result_summary': json.dumps(sources, ensure_ascii=False)[:1000],
                **({'error': '所有搜索源均未返回可用结果'} if not sources else {}),
            })
            if not sources:
                return {'reply': '❌ 联网搜索未返回可用结果，已停止生成和发布，避免凭空编造。',
                        'tool_calls': tool_calls, 'token_usage': {'input': 0, 'output': 0}}
        draft = await _generate(message, history, previous, sources)
        if sources and not previous:
            draft = _attach_sources(draft, sources)

    if publish:
        section_id = await _section_id(draft['post_type'])
        payload = {key: value for key, value in draft.items() if key != 'sources'}
        payload.update({'section_id': section_id, 'author_id': user_id})
        result = await create_post.ainvoke(payload)
        tool_calls.append({'tool_name': 'create_post', 'status': 'success', 'tool_args': payload,
                           'result_summary': str(result)[:500]})
        return {'reply': _display_draft(draft, published=True), 'tool_calls': tool_calls,
                'token_usage': {'input': 0, 'output': 0}}
    return {'reply': _display_draft(draft), 'tool_calls': tool_calls,
            'token_usage': {'input': 0, 'output': 0}}
