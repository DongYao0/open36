"""
Forum Agent - 论坛Agent（帖子创建与管理，含联网搜索）
使用OpenAI兼容API（DeepSeek/Claude等）
"""
import json
import logging

import httpx

from app.config import settings
from app.tools.forum_tools import list_sections, create_post, list_posts, update_post
from app.tools.search_tools import search_web, fetch_url

logger = logging.getLogger(__name__)

# 论坛Agent可用工具定义（OpenAI function calling格式）
FORUM_TOOLS_DEF = [
    {
        'type': 'function',
        'function': {
            'name': 'search_web',
            'description': '联网搜索最新信息。适用于需要查找最新资讯、技术动态等时效性内容。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': '搜索关键词'},
                    'max_results': {'type': 'integer', 'description': '最大返回结果数', 'default': 5},
                },
                'required': ['query'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'fetch_url',
            'description': '抓取网页内容，提取纯文本返回。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string', 'description': '要抓取的网页URL'},
                },
                'required': ['url'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_sections',
            'description': '获取所有启用的板块列表。返回板块的id、name、description等信息。',
            'parameters': {'type': 'object', 'properties': {}},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'create_post',
            'description': '创建论坛帖子。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string', 'description': '帖子标题，5-100字符'},
                    'content': {'type': 'string', 'description': '帖子内容，Markdown格式'},
                    'section_id': {'type': 'integer', 'description': '板块ID'},
                    'author_id': {'type': 'integer', 'description': '作者用户ID'},
                },
                'required': ['title', 'content', 'section_id', 'author_id'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_posts',
            'description': '查询帖子列表。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'section_id': {'type': 'integer', 'description': '板块ID（可选）'},
                    'page': {'type': 'integer', 'description': '页码', 'default': 1},
                    'page_size': {'type': 'integer', 'description': '每页数量', 'default': 20},
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'update_post',
            'description': '编辑论坛帖子。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'post_id': {'type': 'integer', 'description': '帖子ID'},
                    'title': {'type': 'string', 'description': '新标题（可选）'},
                    'content': {'type': 'string', 'description': '新内容（可选）'},
                    'author_id': {'type': 'integer', 'description': '编辑者用户ID'},
                },
                'required': ['post_id'],
            },
        },
    },
]

# 工具函数映射
FORUM_TOOLS_MAP = {
    'search_web': search_web,
    'fetch_url': fetch_url,
    'list_sections': list_sections,
    'create_post': create_post,
    'list_posts': list_posts,
    'update_post': update_post,
}

FORUM_SYSTEM_PROMPT = """你是Open436平台的论坛内容管理Agent。你的职责是根据管理员的指令创建、编辑论坛帖子。

工作规范：
1. 帖子内容使用Markdown格式
2. 技术内容必须准确，代码示例必须可运行
3. 标题简洁有吸引力，5-100字符
4. 内容充实有结构，500-5000字
5. 使用合适的标题、列表、代码块等格式化元素
6. 涉及时效性内容（如"最新"、"近期"）时，先使用search_web搜索最新信息再生成内容

执行流程：
1. 如需搜索最新信息，先调用search_web
2. 调用list_sections获取板块列表，匹配目标板块
3. 生成帖子标题和内容
4. 调用create_post创建帖子
5. 返回执行结果（含帖子ID）"""


async def _call_llm(messages: list, tools: list = None) -> dict:
    """调用OpenAI兼容API"""
    base_url = settings.LLM_BASE_URL or 'https://api.deepseek.com'
    url = f'{base_url}/v1/chat/completions'

    payload = {
        'model': settings.LLM_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 4096,
    }
    if tools:
        payload['tools'] = tools

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {settings.ANTHROPIC_API_KEY}'},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()


async def execute_forum_task(user_message: str, user_id: int) -> dict:
    """
    执行论坛相关任务

    Args:
        user_message: 用户消息
        user_id: 当前管理员ID

    Returns:
        {"reply": "...", "tool_calls": [...], "token_usage": {...}}
    """
    try:
        messages = [
            {'role': 'system', 'content': FORUM_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message},
        ]

        tool_calls_log = []
        token_usage = {'input': 0, 'output': 0}

        # Agent循环：LLM → 工具调用 → LLM → ... 直到返回最终回复
        for _ in range(10):
            data = await _call_llm(messages, FORUM_TOOLS_DEF)

            usage = data.get('usage', {})
            token_usage['input'] += usage.get('prompt_tokens', 0)
            token_usage['output'] += usage.get('completion_tokens', 0)

            choice = data['choices'][0]
            message = choice['message']
            finish_reason = choice.get('finish_reason', '')

            # 如果没有工具调用，说明Agent已完成
            if finish_reason == 'stop' or not message.get('tool_calls'):
                return {
                    'reply': message.get('content', ''),
                    'tool_calls': tool_calls_log,
                    'token_usage': token_usage,
                }

            # 将assistant消息加入历史
            messages.append(message)

            # 执行工具调用
            for tc in message['tool_calls']:
                tool_name = tc['function']['name']
                tool_args_str = tc['function']['arguments']
                tool_id = tc['id']

                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                logger.info(f'调用工具: {tool_name}({tool_args})')

                tool_func = FORUM_TOOLS_MAP.get(tool_name)
                if not tool_func:
                    tool_result = f'未知工具: {tool_name}'
                    tool_calls_log.append({
                        'tool_name': tool_name,
                        'status': 'failed',
                        'error': tool_result,
                    })
                else:
                    try:
                        import time
                        start = time.time()
                        result = await tool_func.ainvoke(tool_args)
                        duration = int((time.time() - start) * 1000)

                        tool_result = str(result)
                        tool_calls_log.append({
                            'tool_name': tool_name,
                            'status': 'success',
                            'duration_ms': duration,
                            'result_summary': tool_result[:200],
                        })
                    except Exception as e:
                        tool_result = f'工具执行失败: {str(e)}'
                        tool_calls_log.append({
                            'tool_name': tool_name,
                            'status': 'failed',
                            'error': str(e),
                        })

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_id,
                    'content': tool_result,
                })

        return {
            'reply': '任务执行超过最大轮数，请简化指令后重试。',
            'tool_calls': tool_calls_log,
            'token_usage': token_usage,
        }

    except Exception as e:
        logger.error(f'Forum Agent执行失败: {e}')
        return {
            'reply': f'论坛Agent执行异常: {str(e)}',
            'tool_calls': [],
            'token_usage': {'input': 0, 'output': 0},
        }
