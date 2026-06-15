"""
多Agent编排 - Orchestrator 架构（理解→规划→委派）

Orchestrator 负责：
1. 深度理解用户意图
2. 规划执行步骤（可能多步）
3. 委派给专业 Agent 执行
4. 步骤间传递上下文（搜索结果→写帖子）
"""
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import TypedDict

from app.config import settings
from app.core.llm import llm
from app.agents.router import orchestrate

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8))


def _now_str() -> str:
    """当前北京时间字符串，用于注入LLM上下文"""
    now = datetime.now(BEIJING_TZ)
    weekdays = '一二三四五六日'
    return now.strftime(f'%Y年%m月%d日 %H:%M:%S 星期{weekdays[now.weekday()]}')


class AgentState(TypedDict):
    """Agent状态"""
    user_message: str
    user_id: int
    intent: str
    agent_name: str
    reply: str
    crawled_data: list[dict]  # 爬虫收集的原始数据
    tool_calls: list[dict]
    token_usage: dict


async def _call_llm(messages: list, tools: list = None) -> dict:
    """调用OpenAI兼容API - 委托给统一客户端"""
    return await llm.chat(messages=messages, tools=tools, temperature=0.3, max_tokens=1024)


async def crawl_node(state: AgentState) -> AgentState:
    """数据收集节点：Router 调用爬虫工具收集数据

    智能判断：
    - 用户消息中有 URL → 并行 crawl_webpage 爬取所有页面
    - 没有 URL → 用 LLM 规划关键词，crawl_search 搜索
    - 爬虫服务不可用时 → 降级到 DuckDuckGo 搜索
    """
    import asyncio
    from app.tools.crawler_tools import crawl_search, crawl_webpage
    from app.tools.search_tools import search_web
    import re as _re

    user_msg = state['user_message']
    crawled = []
    tool_calls_log = []

    try:
        # 检查用户消息中是否有 URL
        url_pattern = r'https?://[^\s<>"\')\]]+'
        urls = _re.findall(url_pattern, user_msg)

        if urls:
            # 有 URL → 并行爬取（asyncio.gather 并发执行）
            urls = urls[:10]  # 最多10个URL

            async def _crawl_one(url: str) -> dict | None:
                logger.info(f'爬取网页: {url}')
                result = await crawl_webpage.ainvoke({'url': url})
                tool_calls_log.append({
                    'tool_name': 'crawl_webpage',
                    'status': 'success' if result.get('success') else 'failed',
                    'url': url,
                })
                return result if result.get('success') else None

            # 并行执行所有爬取任务
            results = await asyncio.gather(*[_crawl_one(url) for url in urls])
            crawled = [r for r in results if r is not None]
            logger.info(f'并行爬取完成: {len(crawled)}/{len(urls)} 成功')
        else:
            # 没有 URL → 用 LLM 规划搜索关键词
            # P0优化：最多2个关键词，每词3篇，够用即停
            plan_prompt = f"""用户请求: {user_msg}

请判断需要搜索哪些关键词来收集数据。

规则：
- 如果用户已经给了明确的搜索词，直接使用
- 优先使用英文关键词（搜索结果更丰富）
- 最多2个关键词（精简高效，避免冗余搜索）
- 不需要搜索则返回空列表

返回JSON：{{"queries": ["关键词1", "关键词2"], "max_results": 3}}"""

            data = await _call_llm([
                {'role': 'system', 'content': '你是数据收集规划师。根据用户请求，规划需要搜索的关键词。只返回JSON。'},
                {'role': 'user', 'content': plan_prompt},
            ])

            content = data['choices'][0]['message']['content'].strip()
            if content.startswith('{'):
                plan = json.loads(content)
            else:
                match = _re.search(r'\{.*\}', content, _re.DOTALL)
                plan = json.loads(match.group()) if match else {'queries': []}

            queries = plan.get('queries', [])
            max_results = min(plan.get('max_results', 3), 3)  # P0: 每词最多3篇

            # P0: 够了就停的阈值
            ENOUGH_PAGES = 5

            # 先尝试爬虫服务，失败则降级到 DuckDuckGo
            use_ddg_fallback = False

            # P0: queries[:3] → queries[:2]，且够了就提前退出
            for query in queries[:2]:
                if len(crawled) >= ENOUGH_PAGES:
                    logger.info(f'已收集{len(crawled)}页，提前结束搜索')
                    break
                logger.info(f'爬取搜索: {query}')
                try:
                    result = await crawl_search.ainvoke({
                        'keyword': query,
                        'max_results': max_results,
                    })
                    tool_calls_log.append({
                        'tool_name': 'crawl_search',
                        'status': 'success' if result.get('success') else 'failed',
                        'query': query,
                        'pages_count': len(result.get('pages', [])),
                    })
                    if result.get('success'):
                        crawled.extend(result.get('pages', []))
                    else:
                        use_ddg_fallback = True
                except Exception as e:
                    logger.warning(f'爬虫服务调用失败，降级到 DuckDuckGo: {e}')
                    use_ddg_fallback = True
                    break

            # 降级方案：使用 DuckDuckGo 搜索
            if (use_ddg_fallback or not crawled) and len(crawled) < ENOUGH_PAGES:
                logger.info('使用 DuckDuckGo 作为降级搜索方案')
                for query in queries[:2]:
                    if len(crawled) >= ENOUGH_PAGES:
                        break
                    try:
                        ddg_results = await search_web.ainvoke({
                            'query': query,
                            'max_results': max_results,
                        })
                        if isinstance(ddg_results, list):
                            for item in ddg_results:
                                if isinstance(item, dict) and item.get('url'):
                                    crawled.append({
                                        'title': item.get('title', ''),
                                        'url': item.get('url', ''),
                                        'markdown': item.get('content', ''),
                                    })
                            tool_calls_log.append({
                                'tool_name': 'search_web',
                                'status': 'success',
                                'query': query,
                                'results_count': len(ddg_results),
                            })
                    except Exception as e:
                        logger.warning(f'DuckDuckGo 搜索失败: {e}')
                        tool_calls_log.append({
                            'tool_name': 'search_web',
                            'status': 'failed',
                            'query': query,
                            'error': str(e),
                        })

        state['crawled_data'] = crawled
        state['tool_calls'] = tool_calls_log
        logger.info(f'爬取完成: {len(crawled)} 个页面')

    except Exception as e:
        logger.error(f'数据收集失败: {e}')
        state['crawled_data'] = []
        state['tool_calls'] = [{'tool_name': 'crawl', 'status': 'failed', 'error': str(e)}]

    return state


async def forum_node(state: AgentState, history: list[dict] = None) -> AgentState:
    """论坛Agent：纯加工，接收爬取数据生成帖子"""
    from app.agents.forum import execute_forum_task_with_data

    result = await execute_forum_task_with_data(
        user_message=state['user_message'],
        user_id=state['user_id'],
        crawled_data=state.get('crawled_data', []),
    )
    state['agent_name'] = 'forum'
    state['reply'] = result['reply']
    state['tool_calls'].extend(result.get('tool_calls', []))
    state['token_usage'] = result['token_usage']
    return state


async def problem_node(state: AgentState, history: list[dict] = None) -> AgentState:
    """出题Agent：纯加工，接收爬取数据生成题目"""
    from app.agents.problem import execute_problem_task_with_data

    result = await execute_problem_task_with_data(
        user_message=state['user_message'],
        user_id=state['user_id'],
        crawled_data=state.get('crawled_data', []),
        history=history,
    )
    state['agent_name'] = 'problem'
    state['reply'] = result['reply']
    state['tool_calls'].extend(result.get('tool_calls', []))
    state['token_usage'] = result['token_usage']
    return state


CHAT_SYSTEM_PROMPT = """你是Open436平台的AI助手小46。你性格友好、专业、简洁。

能力范围：
- 日常对话、知识问答、代码问题、计算问题
- 涉及平台操作时，引导用户使用具体功能（如"你可以用搜索功能找题"）

回复风格：
- 简洁自然，不要过度使用markdown格式
- 直接回答问题，不要加"作为AI助手"之类的开场白
- 如果不确定，诚实说明"""


async def chat_node(state: AgentState, history: list[dict] = None) -> AgentState:
    """通用聊天节点：直接对话，不走爬虫（注入当前时间）"""
    try:
        # 注入当前北京时间，让模型能回答"现在几点/今天日期"等
        system_content = f'{CHAT_SYSTEM_PROMPT}\n\n【当前时间】{_now_str()}（北京时间）。'
        messages = [{'role': 'system', 'content': system_content}]
        if history:
            messages.extend(history[-10:])
        messages.append({'role': 'user', 'content': state['user_message']})

        data = await llm.chat(messages=messages, temperature=0.7, max_tokens=1024, timeout=30.0)
        reply = data['choices'][0]['message']['content'].strip()
        usage = data.get('usage', {})

        state['agent_name'] = 'chat'
        state['reply'] = reply
        state['tool_calls'] = []
        state['token_usage'] = {
            'input': usage.get('prompt_tokens', 0),
            'output': usage.get('completion_tokens', 0),
        }
    except Exception as e:
        logger.error(f'聊天Agent异常: {e}')
        state['agent_name'] = 'chat'
        state['reply'] = f'抱歉，处理消息时出现问题：{str(e)}'
        state['tool_calls'] = []
        state['token_usage'] = {'input': 0, 'output': 0}

    return state


async def chat_node_stream(state: AgentState, history: list[dict] = None):
    """流式聊天节点 - yield delta chunks"""
    system_content = f'{CHAT_SYSTEM_PROMPT}\n\n【当前时间】{_now_str()}（北京时间）。'
    messages = [{'role': 'system', 'content': system_content}]
    if history:
        messages.extend(history[-10:])
    messages.append({'role': 'user', 'content': state['user_message']})

    async for delta in llm.chat_stream(messages=messages, temperature=0.7, max_tokens=1024, timeout=60.0):
        yield delta


async def query_node(state: AgentState) -> AgentState:
    """查询节点"""
    state['agent_name'] = 'router'
    state['reply'] = f'收到您的查询："{state["user_message"]}"。查询功能正在完善中。'
    state['tool_calls'] = []
    state['token_usage'] = {'input': 0, 'output': 0}
    return state


async def unclear_node(state: AgentState) -> AgentState:
    """澄清节点"""
    state['agent_name'] = 'router'
    state['reply'] = (
        '抱歉，我没有完全理解您的指令。您可以：\n'
        '- 直接描述需求，例如"帮我搜集XXX资料发个帖子"或"生成一道算法题"\n'
        '- 或者直接和我聊天也可以哦'
    )
    state['tool_calls'] = []
    state['token_usage'] = {'input': 0, 'output': 0}
    return state


def _patch_outdated_models(reply: str) -> str:
    """后处理：替换过时版本号 + 检测时间矛盾"""
    import re
    import sys
    from datetime import datetime

    sys.stderr.write(f'[_patch] called, reply length: {len(reply)}\n')
    sys.stderr.flush()

    # Claude 模型版本映射（过时 → 最新）
    claude_patches = [
        (r'Claude 3\.5 Sonnet', 'Claude 4.X Sonnet (Sonnet 4.6) [官方已知]'),
        (r'Claude 3\.5 Opus', 'Claude 4.X Opus (Opus 4.8) [官方已知]'),
        (r'Claude 3\.5 Haiku', 'Claude 4.X Haiku (Haiku 4.5) [官方已知]'),
        (r'Claude 3 Sonnet(?!\s*4)', 'Claude 4.X Sonnet (Sonnet 4.6) [官方已知]'),
        (r'Claude 3 Opus(?!\s*4)', 'Claude 4.X Opus (Opus 4.8) [官方已知]'),
        (r'Claude 3 Haiku(?!\s*4)', 'Claude 4.X Haiku (Haiku 4.5) [官方已知]'),
        (r'Claude 3\.7 Sonnet', 'Claude 4.X Sonnet (Sonnet 4.6) [官方已知]'),
    ]

    for pattern, replacement in claude_patches:
        reply = re.sub(pattern, replacement, reply)

    # 如果回复中提到"最新模型是Claude 3.x"，追加说明
    if re.search(r'最新.*Claude 3\.[0-9]', reply):
        reply += '\n\n⚠️ 注意：以上搜索结果可能过时。Claude 当前最新家族为 Claude 4.X（Opus 4.8, Sonnet 4.6, Haiku 4.5）[官方已知]。'

    # 时间矛盾检测：回复中提到"将于/即将/尚未开始"等未来时态，但当前已过该日期
    now = datetime.now(BEIJING_TZ)
    # 匹配 "X月X日" 格式
    date_matches = re.findall(r'(\d{1,2})月(\d{1,2})日', reply)
    for month_str, day_str in date_matches:
        month, day = int(month_str), int(day_str)
        try:
            mentioned_date = datetime(now.year, month, day, tzinfo=BEIJING_TZ)
            # 如果提到的日期已过，且回复中有"将于/即将/尚未"等未来时态词
            if mentioned_date < now and re.search(r'将于|即将|尚未开始|还没有开始|还没开始|即将开始', reply):
                sys.stderr.write(f'[_patch] time contradiction detected: {month}月{day}日 already passed\n')
                sys.stderr.flush()
                reply += f'\n\n⚠️ 注意：当前时间是{now.strftime("%Y年%m月%d日")}，{month}月{day}日已过。以上信息可能来自早期报道，建议搜索最新结果。'
                break
        except ValueError:
            pass

    sys.stderr.write(f'[_patch] done, has 4.X: {"4.X" in reply}\n')
    sys.stderr.flush()
    return reply


async def search_node(state: AgentState, history: list[dict] = None) -> AgentState:
    """搜索节点：LLM + CrawlerService 联网搜索，优先用搜索结果，LLM 知识作为补充"""
    from app.tools.crawler_tools import crawl_search

    crawled = state.get('crawled_data', [])
    user_msg = state['user_message']

    # 如果没有爬取数据，用 CrawlerService 搜索补充（默认 Bing，结果更新）
    if not crawled:
        try:
            # 用 LLM 生成搜索关键词（智能补年份，提升时效性）
            current_year = _now_str()[:4]
            kw_data = await _call_llm([
                {'role': 'system', 'content': f'''根据用户问题，生成最有效的搜索关键词。

时间处理规则（核心）：
1. 用户已给出具体时间/年份 → 直接使用，不要改
   例："25年最厉害的国产模型" → 关键词含 "2025"
2. 用户未给时间，但涉及"最新/现在/当前/版本/latest/newest/current/什么时候/几点/今天"等时效词 → 自动加当前年份 {current_year}
   例："世界杯什么时候开始" → 关键词含 "{current_year}"
   例："Claude最新模型" → 关键词含 "{current_year}"
3. 纯知识/历史问题（不涉及时效）→ 不加年份
   例："Python怎么排序" → 不加年份

其他规则：
- 优先使用英文关键词（搜索结果更丰富）
- 只返回关键词，不要其他内容'''},
                {'role': 'user', 'content': user_msg},
            ])
            keyword = kw_data['choices'][0]['message']['content'].strip().strip('"')
            logger.info(f'搜索关键词: {keyword}')

            # 使用 SearXNG 搜索（聚合 Google/Bing/DuckDuckGo 等多引擎）
            from app.tools.search_tools import search_web
            search_result = await search_web.ainvoke({'query': keyword, 'max_results': 8})
            if isinstance(search_result, list):
                for item in search_result:
                    if isinstance(item, dict) and item.get('url'):
                        crawled.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'markdown': item.get('content', ''),
                        })
                logger.info(f'SearXNG搜索完成: {len(crawled)} 个结果')
        except Exception as e:
            logger.warning(f'联网搜索失败: {e}')

    # 构建上下文：爬取数据（如有）
    crawled_context = ''
    if crawled:
        context_parts = []
        for i, page in enumerate(crawled[:10], 1):
            title = page.get('title', '无标题')
            url = page.get('url', '')
            content = (page.get('markdown') or page.get('content') or '')[:3000]
            context_parts.append(f'--- {title} ---\n来源: {url}\n{content}')
        crawled_context = '\n\n'.join(context_parts)

    # 用 LLM 基于搜索结果回答（强制接地：以搜索为准，标注来源）
    now_str = _now_str()
    if crawled_context:
        prompt = f"""用户请求: {user_msg}

当前时间：{now_str}

以下是实时搜索到的参考内容（可能过时）：
{crawled_context}

⚠️ 重要规则：
1. 【时间推理】搜索结果中的日期/时间必须与当前时间对比：
   - 若搜索结果说"将于X月X日开始"，而当前时间已过该日期 → 说明已经开始，应搜索最新结果
   - 若搜索结果说"已于X月X日结束"，而当前时间在该日期之前 → 说明尚未结束
   - 绝不能照搬搜索结果的未来/过去时态，必须结合当前时间判断
2. 搜索结果中的版本号若明显过时（如仍显示旧版本），必须使用以下已知最新信息替代：
   - Claude 最新家族：Claude 4.X（Opus 4.8, Sonnet 4.6, Haiku 4.5）[官方已知]
   - GPT 最新：GPT-4o / GPT-4.1 [官方已知]
3. 搜索结果仍有效的内容，直接展示来源名称和URL。
3. 综合两方面信息回答，以已知最新信息为准。

输出要求：
- 严格按照用户要求的格式
- 干净整洁
- **来源必须直接展示**：不要用[来源N]隐藏，直接写"来源：XXX（URL）"
- 示例：`**来源：** 洛谷P1001 https://www.luogu.com.cn/problem/P1001`"""
    else:
        prompt = f"""用户请求: {user_msg}

⚠️ 本次搜索未返回任何结果。请诚实处理：
1. 不要用训练记忆编造时效性信息（版本号、价格、当前事件）。
2. 明确告知："未能搜索到相关结果，以下是基于我已有知识的回答（可能不是最新）"。
3. 涉及最新/版本/价格的内容，建议用户换关键词重试或自行核实。

请基于你的知识回答，但开头必须标注"以下信息可能不是最新"。

输出要求：
- 严格按照用户要求的格式
- 干净整洁"""

    try:
        system_prompt = """你是严谨的信息检索助手。回答的核心事实优先基于搜索结果，直接展示来源名称和URL。

**重要：当用户要求"找题/搜题/看题"时**：
- 用户想要的是**题目内容**，不是解题思路
- **【强制要求】必须严格按照用户要求的数量返回题目**（如"找两道题"就必须返回2道，"找三道题"就必须返回3道，不能少）
- 如果搜索结果不足，**必须**基于你的算法知识补充题目（确保题目准确、符合要求）
- **注意：返回题目数量不足 = 任务失败！** 用户说几道就必须返回几道
- 输出格式：题目标题、题目描述、输入格式、输出格式、样例输入输出
- 不要输出解题思路、代码实现、算法分析
- 每道题用清晰的结构展示，用"## 题目1"、"## 题目2"等分隔
- **来源必须直接展示**：不要用[来源N]隐藏，直接写"来源：XXX（URL）"
- 示例：`**来源：** 洛谷P1001 https://www.luogu.com.cn/problem/P1001` 或 `**来源：** [基于算法知识]`

示例输出格式：
---
## 题目1：XXX

**题目描述：**
...

**输入格式：**
...

**输出格式：**
...

**样例输入：**
```
...
```

**样例输出：**
```
...
```

**来源：** [来源N]
---

禁止用训练记忆编造时效性信息。"""
        data = await _call_llm([
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt},
        ])
        reply = data['choices'][0]['message']['content'].strip()

        # 后处理：替换过时的模型版本号
        reply = _patch_outdated_models(reply)

        usage = data.get('usage', {})
        token_usage = {
            'input': usage.get('prompt_tokens', 0),
            'output': usage.get('completion_tokens', 0),
        }
    except Exception as e:
        logger.error(f'Search LLM 处理失败: {e}')
        if crawled:
            reply_parts = [f'共找到 {len(crawled)} 个结果：\n']
            for i, page in enumerate(crawled[:5], 1):
                title = page.get('title', '无标题')
                url = page.get('url', '')
                reply_parts.append(f'{i}. {title}\n{url}\n')
            reply = '\n'.join(reply_parts)
        else:
            reply = f'抱歉，处理失败: {str(e)}'
        token_usage = {'input': 0, 'output': 0}

    state['agent_name'] = 'search'
    state['reply'] = reply
    state['tool_calls'] = []
    state['token_usage'] = token_usage
    return state


async def search_node_stream(state: AgentState):
    """搜索节点流式版：先爬取，再流式生成回答

    Yields:
        str: 内容片段
    """
    from app.tools.search_tools import search_web

    crawled = state.get('crawled_data', [])
    user_msg = state['user_message']

    # 如果没有爬取数据，用 SearXNG 搜索补充
    if not crawled:
        try:
            current_year = _now_str()[:4]
            kw_data = await _call_llm([
                {'role': 'system', 'content': f'根据用户问题，生成最有效的搜索关键词。规则：\n1. 优先使用英文关键词\n2. 涉及"最新/现在/当前/版本/latest"时，加当前年份 {current_year}\n3. 只返回关键词'},
                {'role': 'user', 'content': user_msg},
            ])
            keyword = kw_data['choices'][0]['message']['content'].strip().strip('"')
            logger.info(f'[stream] 搜索关键词: {keyword}')

            search_result = await search_web.ainvoke({'query': keyword, 'max_results': 8})
            if isinstance(search_result, list):
                for item in search_result:
                    if isinstance(item, dict) and item.get('url'):
                        crawled.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'markdown': item.get('content', ''),
                        })
                logger.info(f'[stream] SearXNG搜索完成: {len(crawled)} 个结果')
        except Exception as e:
            logger.warning(f'[stream] 联网搜索失败: {e}')

    # 构建上下文
    crawled_context = ''
    if crawled:
        context_parts = []
        for i, page in enumerate(crawled[:10], 1):
            title = page.get('title', '无标题')
            url = page.get('url', '')
            content = (page.get('markdown') or page.get('content') or '')[:3000]
            context_parts.append(f'--- 来源 {i}: {title} ({url}) ---\n{content}')
        crawled_context = '\n\n'.join(context_parts)

    # 流式生成回答
    now_str = _now_str()
    if crawled_context:
        prompt = f"""用户请求: {user_msg}

当前时间：{now_str}

以下是实时搜索到的参考内容（可能过时）：
{crawled_context}

⚠️ 重要规则：
1. 【时间推理】搜索结果中的日期/时间必须与当前时间对比
2. 搜索结果中的版本号若明显过时，使用已知最新信息替代
3. 搜索结果仍有效的内容，标注[来源N]

输出要求：
- 严格按照用户要求的格式
- 干净整洁
- 关键事实后附 [来源N] 或 [官方已知]"""
    else:
        prompt = f"""用户请求: {user_msg}

当前时间：{now_str}

⚠️ 本次搜索未返回任何结果。请基于你的知识回答，但开头必须标注"以下信息可能不是最新"。"""

    try:
        system_prompt = '你是严谨的信息检索助手。回答的核心事实优先基于搜索结果，并标注来源[来源N]。当搜索结果明显过时时，使用已知最新信息并标注[官方已知]。'
        full_reply = ''
        async for delta in llm.chat_stream(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.7,
            max_tokens=2048,
            timeout=60.0,
        ):
            content = delta.get('content', '')
            if content:
                full_reply += content
                yield content

        # 流结束后后处理
        full_reply = _patch_outdated_models(full_reply)
        state['agent_name'] = 'search'
        state['reply'] = full_reply
        state['tool_calls'] = []
        state['token_usage'] = {'input': 0, 'output': 0}
    except Exception as e:
        logger.error(f'[stream] Search LLM 处理失败: {e}')
        error_msg = f'抱歉，处理失败: {str(e)}'
        yield error_msg
        state['agent_name'] = 'search'
        state['reply'] = error_msg
        state['tool_calls'] = []
        state['token_usage'] = {'input': 0, 'output': 0}


async def _execute_step(step: dict, user_id: int, crawled_data: list[dict],
                        history: list[dict] = None) -> AgentState:
    """执行单个步骤：根据 agent 类型分发到对应节点"""
    agent = step.get('agent', 'chat')
    task_input = step.get('input', step.get('task', ''))

    state: AgentState = {
        'user_message': task_input,
        'user_id': user_id,
        'intent': agent,
        'agent_name': agent,
        'reply': '',
        'crawled_data': crawled_data,
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }

    if agent == 'forum':
        state = await forum_node(state, history=history)
    elif agent == 'problem':
        state = await problem_node(state, history=history)
    elif agent == 'search':
        state = await search_node(state, history=history)
    elif agent == 'query':
        state = await query_node(state)
    elif agent == 'chat':
        state = await chat_node(state, history=history)
    else:
        state = await unclear_node(state)

    return state


def _should_crawl_for_step(step: dict) -> bool:
    """判断某个步骤是否需要先爬取数据"""
    agent = step.get('agent', 'chat')
    task = step.get('task', '') + step.get('input', '')

    if agent not in ('forum', 'problem', 'search'):
        return False

    # 有 URL → 需要爬取
    if re.search(r'https?://[^\s<>"\')\]]+', task):
        return True

    # search agent 始终需要
    if agent == 'search':
        return True

    # forum/problem 无 URL → 让 agent 自己决定（可能不需要搜索）
    return False


async def run_agent(user_message: str, user_id: int, history: list[dict] = None) -> dict:
    """
    执行Agent工作流 - Orchestrator 架构（理解→规划→委派）

    Args:
        user_message: 用户消息
        user_id: 用户ID
        history: 历史消息列表

    Returns:
        {reply, intent, agent_name, tool_calls, token_usage}
    """
    import sys
    sys.stderr.write(f'[run_agent] ENTER called\n')
    sys.stderr.flush()

    # Step 1: Orchestrator 理解任务 + 规划步骤
    plan = await orchestrate(user_message)
    steps = plan.get('steps', [])
    logger.info(f'Orchestrator 规划: {plan.get("understanding")} → {len(steps)} 步')

    if not steps:
        steps = [{'step': 1, 'agent': 'unclear', 'task': user_message, 'input': user_message}]

    # Step 2: 逐步执行，传递上下文
    all_crawled = []
    all_tool_calls = []
    total_tokens = {'input': 0, 'output': 0}
    step_results = []  # 每步的结果，供后续步骤参考

    for step in steps:
        agent = step.get('agent', 'chat')
        step_input = step.get('input', step.get('task', ''))

        # 如果 input 引用了前序步骤的结果，替换为实际内容
        for i, prev_result in enumerate(step_results):
            placeholder = f'step {i+1}'
            if placeholder in step_input.lower() or f'步骤{i+1}' in step_input:
                # 把前序结果作为上下文注入
                step_input = f'{step_input}\n\n前序步骤结果:\n{prev_result["reply"][:2000]}'
                step['input'] = step_input

        # 判断是否需要爬取
        if _should_crawl_for_step(step):
            crawl_state: AgentState = {
                'user_message': step_input,
                'user_id': user_id,
                'intent': agent,
                'agent_name': 'crawl',
                'reply': '',
                'crawled_data': [],
                'tool_calls': [],
                'token_usage': {'input': 0, 'output': 0},
            }
            crawl_state = await crawl_node(crawl_state)
            all_crawled.extend(crawl_state.get('crawled_data', []))
            all_tool_calls.extend(crawl_state.get('tool_calls', []))

        # 执行步骤
        state = await _execute_step(step, user_id, all_crawled, history)
        step_results.append(state)

        all_tool_calls.extend(state.get('tool_calls', []))
        total_tokens['input'] += state['token_usage'].get('input', 0)
        total_tokens['output'] += state['token_usage'].get('output', 0)

    # Step 3: 汇总结果
    if len(step_results) == 1:
        # 单步骤：直接返回
        final = step_results[0]
    else:
        # 多步骤：合并回复
        replies = []
        for i, result in enumerate(step_results):
            if result['reply']:
                replies.append(result['reply'])
        final_reply = '\n\n'.join(replies)
        final = {
            'reply': final_reply,
            'agent_name': step_results[-1]['agent_name'],
        }

    # 后处理：替换过时的模型版本号
    final_reply = _patch_outdated_models(final['reply'])

    return {
        'reply': final_reply,
        'intent': steps[-1].get('agent', 'chat'),
        'agent_name': final['agent_name'],
        'tool_calls': all_tool_calls,
        'token_usage': total_tokens,
    }


async def run_agent_stream(user_message: str, user_id: int, history: list[dict] = None):
    """流式执行Agent工作流 - Orchestrator 架构

    Yields:
        dict: {'type': 'content', 'content': '...'} 或 {'type': 'meta', ...}
    """
    # Step 1: Orchestrator 理解任务 + 规划步骤
    plan = await orchestrate(user_message)
    steps = plan.get('steps', [])
    logger.info(f'[stream] Orchestrator 规划: {plan.get("understanding")} → {len(steps)} 步')

    if not steps:
        steps = [{'step': 1, 'agent': 'unclear', 'task': user_message, 'input': user_message}]

    # 发送规划元数据
    yield {'type': 'meta', 'understanding': plan.get('understanding', ''), 'steps': len(steps)}

    # Step 2: 逐步执行
    all_crawled = []
    step_results = []

    for step in steps:
        agent = step.get('agent', 'chat')
        step_input = step.get('input', step.get('task', ''))

        # 替换前序步骤引用
        for i, prev_result in enumerate(step_results):
            placeholder = f'step {i+1}'
            if placeholder in step_input.lower() or f'步骤{i+1}' in step_input:
                step_input = f'{step_input}\n\n前序步骤结果:\n{prev_result["reply"][:2000]}'

        # 爬取
        if _should_crawl_for_step(step):
            crawl_state: AgentState = {
                'user_message': step_input,
                'user_id': user_id,
                'intent': agent,
                'agent_name': 'crawl',
                'reply': '',
                'crawled_data': [],
                'tool_calls': [],
                'token_usage': {'input': 0, 'output': 0},
            }
            crawl_state = await crawl_node(crawl_state)
            all_crawled.extend(crawl_state.get('crawled_data', []))

        # 执行
        state: AgentState = {
            'user_message': step_input,
            'user_id': user_id,
            'intent': agent,
            'agent_name': agent,
            'reply': '',
            'crawled_data': all_crawled,
            'tool_calls': [],
            'token_usage': {'input': 0, 'output': 0},
        }

        if agent == 'chat':
            full_reply = ''
            async for delta in chat_node_stream(state, history=history):
                content = delta.get('content', '')
                if content:
                    full_reply += content
                    yield {'type': 'content', 'content': content}
            state['reply'] = full_reply
        elif agent == 'search':
            # search 真流式：先爬取，再流式生成
            full_reply = ''
            async for content in search_node_stream(state):
                if content:
                    full_reply += content
                    yield {'type': 'content', 'content': content}
            state['reply'] = full_reply
        else:
            state = await _execute_step(step, user_id, all_crawled, history)
            # 分块输出
            reply = state['reply']
            chunk_size = 50
            for i in range(0, len(reply), chunk_size):
                yield {'type': 'content', 'content': reply[i:i+chunk_size]}

        step_results.append(state)

    # 最终元数据
    yield {
        'type': 'done',
        'intent': steps[-1].get('agent', 'chat'),
        'agent_name': step_results[-1]['agent_name'] if step_results else 'unknown',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }
