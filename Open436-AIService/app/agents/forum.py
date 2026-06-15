"""
Forum Agent - 论坛Agent（帖子创建与管理，含联网搜索）
使用OpenAI兼容API（DeepSeek/Claude等）
"""
import json
import logging

from app.core.llm import llm
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

FORUM_SYSTEM_PROMPT = """你是Open436平台的论坛内容管理Agent。你的职责是根据资料生成高质量论坛帖子。

帖子质量标准：
1. 标题：简洁有吸引力，5-100字符，能概括核心内容
2. 内容：500-5000字，结构清晰，有深度
3. 代码：技术内容的代码示例必须可运行、有注释
4. 原创：综合多个来源，不要直接复制，要有自己的分析和总结

⚠️ 格式要求（严格遵守，输出纯正文风格）：
- 禁止使用 # ## ### 等Markdown标题语法！标题太大会打乱排版
- 用阿拉伯数字划分层级：一、二、三 或 1. 2. 3. 作为段落标题，加粗即可
- 禁止连续空行：段落之间最多1个空行，不要2个以上
- 善用 **加粗** 突出关键词，用行内 `代码` 标记技术术语
- 代码块必须标注语言（```python 等）
- 结尾加简短总结，不要突然结束

示例格式（照此风格，禁止用#）：
**一、核心概念**

这里是一段介绍，**关键内容**加粗，`技术术语`用行内代码。要点如下：
- 第一点说明
- 第二点说明

**二、实战代码**

```python
# 示例代码，有注释
def example():
    pass
```

**三、总结**

- 要点一
- 要点二

板块选择规则：
- 技术交流：编程技术、开发经验、技术趋势
- 资源分享：工具、教程、开源项目推荐"""


async def _call_llm(messages: list, tools: list = None) -> dict:
    """调用OpenAI兼容API - 委托给统一客户端"""
    return await llm.chat(messages=messages, tools=tools, temperature=0.7, max_tokens=4096)


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


async def execute_forum_task_with_data(user_message: str, user_id: int, crawled_data: list[dict]) -> dict:
    """
    执行论坛任务（带爬取数据）- 快速模式

    优化：预取板块列表 → LLM 一次性生成帖子 → create_post
    只需 1 次 LLM 调用，耗时从 ~3分钟降到 ~1分钟
    """
    import time as _time
    import re as _re

    try:
        start_total = _time.time()

        # Step 1: 预取板块列表（不经过 LLM）
        sections_data = await list_sections.ainvoke({})
        sections_info = ''
        if isinstance(sections_data, dict) and sections_data.get('code') == 200:
            for s in sections_data.get('data', {}).get('sections', []):
                sections_info += f"- ID:{s['id']} 名称:{s['name']} 描述:{s.get('description','')}\n"
        else:
            sections_info = '- ID:1 名称:技术交流\n'

        # Step 2: 格式化爬取数据
        context_parts = []
        for i, page in enumerate(crawled_data[:10], 1):
            title = page.get('title', '无标题')
            url = page.get('url', '')
            content = (page.get('markdown') or '')[:2000]
            context_parts.append(f'--- 来源 {i}: {title} ({url}) ---\n{content}')

        crawled_context = '\n\n'.join(context_parts) if context_parts else '（无爬取数据，请根据用户描述生成内容）'

        # Step 3: LLM 一次性生成帖子内容（JSON 格式）
        gen_prompt = f"""用户请求: {user_message}

参考资料（共{len(crawled_data)}篇）：
{crawled_context}

可用板块（选择最匹配的一个）：
{sections_info}

任务：根据参考资料生成一篇高质量论坛帖子。

帖子要求：
1. 标题：简洁有吸引力，概括核心内容
2. 结构：有清晰的段落划分，使用标题/列表/代码块
3. 内容：综合多个来源，加入自己的分析和总结，不要直接复制
4. 代码：如果涉及编程，代码示例必须可运行、有注释
5. 字数：500-3000字

返回 JSON 格式（只返回 JSON，不要其他内容）：
{{"title": "帖子标题", "content": "帖子正文(Markdown格式)", "section_id": 板块ID}}"""

        data = await _call_llm([
            {'role': 'system', 'content': '你是技术内容创作专家。根据参考资料生成高质量论坛帖子。只返回 JSON，不要其他内容。'},
            {'role': 'user', 'content': gen_prompt},
        ])

        content = data['choices'][0]['message']['content'].strip()
        usage = data.get('usage', {})
        token_usage = {
            'input': usage.get('prompt_tokens', 0),
            'output': usage.get('completion_tokens', 0),
        }

        # 解析 JSON（处理 LLM 可能返回 ```json 代码块的情况）
        json_str = content
        # 去掉可能的 markdown 代码块标记
        if '```' in json_str:
            json_str = _re.sub(r'```json?\s*', '', json_str)
            json_str = json_str.replace('```', '').strip()
        if json_str.startswith('{'):
            post_data = json.loads(json_str)
        else:
            match = _re.search(r'\{.*\}', json_str, _re.DOTALL)
            post_data = json.loads(match.group()) if match else {}

        title = post_data.get('title', '未命名帖子')
        post_content = post_data.get('content', '')
        section_id = post_data.get('section_id', 1)

        # Step 4: 调用 create_post 发布
        post_result = await create_post.ainvoke({
            'title': title,
            'content': post_content,
            'section_id': section_id,
            'author_id': user_id,
        })

        duration = int((_time.time() - start_total) * 1000)

        post_id = None
        if isinstance(post_result, dict) and post_result.get('code') == 200:
            post_id = post_result.get('data', {}).get('id')

        reply = f'✅ 帖子创建成功！\n\n| 项目 | 内容 |\n|------|------|\n| **帖子ID** | {post_id} |\n| **标题** | {title} |\n| **板块ID** | {section_id} |\n| **耗时** | {duration/1000:.1f}秒 |'

        return {
            'reply': reply,
            'tool_calls': [
                {'tool_name': 'list_sections', 'status': 'success'},
                {'tool_name': 'create_post', 'status': 'success', 'post_id': post_id},
            ],
            'token_usage': token_usage,
        }

    except Exception as e:
        logger.error(f'Forum Agent(with data)执行失败: {type(e).__name__}: {e}', exc_info=True)
        error_msg = str(e) or type(e).__name__
        return {
            'reply': f'论坛Agent执行异常: {error_msg}',
            'tool_calls': [],
            'token_usage': {'input': 0, 'output': 0},
        }
