"""
LangGraph 节点实现 - 主图各节点的执行逻辑

节点签名统一为 (state: AgentState) -> dict（LangGraph 节点约定，返回需更新的字段）。
reducer 字段（crawled_data/tool_calls/step_results）由 StateGraph 自动累加。
"""
import json
import logging
import re
from datetime import datetime, timezone, timedelta

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.core.llm import get_chat_model
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8))

CHAT_SYSTEM_PROMPT = """你是Open436平台的AI助手小46。你性格友好、专业、简洁。

能力范围：
- 日常对话、知识问答、代码问题、计算问题
- 涉及平台操作时，引导用户使用具体功能（如"你可以用搜索功能找题"）

回复风格：
- 简洁自然，不要过度使用markdown格式
- 直接回答问题，不要加"作为AI助手"之类的开场白
- 如果不确定，诚实说明"""


def _now_str() -> str:
    """当前北京时间字符串，用于注入 LLM 上下文"""
    now = datetime.now(BEIJING_TZ)
    weekdays = '一二三四五六日'
    return now.strftime(f'%Y年%m月%d日 %H:%M:%S 星期{weekdays[now.weekday()]}')


def _patch_outdated_models(reply: str) -> str:
    """后处理：替换过时模型版本号 + 时间矛盾检测（已清理旧版 sys.stderr 调试打印）"""
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

    if re.search(r'最新.*Claude 3\.[0-9]', reply):
        reply += '\n\n⚠️ 注意：以上搜索结果可能过时。Claude 当前最新家族为 Claude 4.X（Opus 4.8, Sonnet 4.6, Haiku 4.5）[官方已知]。'

    now = datetime.now(BEIJING_TZ)
    for month_str, day_str in re.findall(r'(\d{1,2})月(\d{1,2})日', reply):
        month, day = int(month_str), int(day_str)
        try:
            mentioned = datetime(now.year, month, day, tzinfo=BEIJING_TZ)
            if mentioned < now and re.search(r'将于|即将|尚未开始|还没有开始|还没开始|即将开始', reply):
                reply += f'\n\n⚠️ 注意：当前时间是{now.strftime("%Y年%m月%d日")}，{month}月{day}日已过。以上信息可能来自早期报道，建议搜索最新结果。'
                break
        except ValueError:
            pass
    return reply


def _history_to_messages(history: list[dict]):
    """把 {role,content} dict 历史转为 LangChain Message 列表"""
    out = []
    for m in (history or [])[-10:]:
        role, content = m.get('role'), m.get('content', '')
        if role == 'user':
            out.append(HumanMessage(content=content))
        elif role == 'assistant':
            out.append(AIMessage(content=content))
    return out


async def chat_node(state: AgentState) -> dict:
    """通用聊天节点：直接对话（注入当前时间）"""
    try:
        system_content = f'{CHAT_SYSTEM_PROMPT}\n\n【当前时间】{_now_str()}（北京时间）。'
        messages = [SystemMessage(content=system_content)]
        messages.extend(_history_to_messages(state.get('history')))
        messages.append(HumanMessage(content=state['user_message']))

        chat_model = get_chat_model(temperature=0.7, max_tokens=1024, streaming=True).with_config(tags=['stream_to_user'])
        msg = await chat_model.ainvoke(messages)
        usage = getattr(msg, 'usage_metadata', None) or {}
        return {
            'agent_name': 'chat',
            'intent': 'chat',
            'reply': (msg.content or '').strip(),
            'token_usage': {'input': usage.get('input_tokens', 0), 'output': usage.get('output_tokens', 0)},
        }
    except Exception as e:
        logger.error(f'聊天Agent异常: {e}')
        return {'agent_name': 'chat', 'intent': 'chat',
                'reply': f'抱歉，处理消息时出现问题：{str(e)}',
                'token_usage': {'input': 0, 'output': 0}}


async def query_node(state: AgentState) -> dict:
    """查询节点（平台内部数据，待完善）"""
    return {'agent_name': 'query', 'intent': 'query',
            'reply': f'收到您的查询："{state["user_message"]}"。查询功能正在完善中。',
            'token_usage': {'input': 0, 'output': 0}}


async def unclear_node(state: AgentState) -> dict:
    """澄清节点"""
    return {'agent_name': 'unclear', 'intent': 'unclear',
            'reply': ('抱歉，我没有完全理解您的指令。您可以：\n'
                      '- 直接描述需求，例如"帮我搜集XXX资料发个帖子"或"生成一道算法题"\n'
                      '- 或者直接和我聊天也可以哦'),
            'token_usage': {'input': 0, 'output': 0}}


async def crawl_node(state: AgentState) -> dict:
    """数据收集：URL→并行爬取；无URL→LLM规划关键词→搜索，失败降级 DuckDuckGo"""
    import asyncio
    from app.tools.crawler_tools import crawl_search, crawl_webpage
    from app.tools.search_tools import search_web

    user_msg = state['user_message']
    crawled, tool_calls = [], []

    try:
        urls = re.findall(r'https?://[^\s<>"\')\]]+', user_msg)
        if urls:
            urls = urls[:10]

            async def _one(u):
                r = await crawl_webpage.ainvoke({'url': u})
                tool_calls.append({'tool_name': 'crawl_webpage',
                                   'status': 'success' if r.get('success') else 'failed', 'url': u})
                return r if r.get('success') else None

            crawled = [r for r in await asyncio.gather(*[_one(u) for u in urls]) if r]
            logger.info(f'并行爬取完成: {len(crawled)}/{len(urls)} 成功')
            return {'crawled_data': crawled, 'tool_calls': tool_calls}

        # 无 URL：LLM 规划关键词
        plan_msg = await get_chat_model().ainvoke([
            SystemMessage(content='你是数据收集规划师。根据用户请求规划搜索关键词（最多2个，优先英文），只返回JSON {"queries":["..."],"max_results":3}。'),
            HumanMessage(content=user_msg),
        ])
        try:
            pdata = json.loads(plan_msg.content.strip())
        except Exception:
            m = re.search(r'\{.*\}', plan_msg.content, re.DOTALL)
            pdata = json.loads(m.group()) if m else {'queries': []}
        queries = pdata.get('queries', [])[:2]
        max_results = min(pdata.get('max_results', 3), 3)
        enough = 5

        for q in queries:
            if len(crawled) >= enough:
                break
            try:
                r = await crawl_search.ainvoke({'keyword': q, 'max_results': max_results})
                tool_calls.append({'tool_name': 'crawl_search', 'status': 'success' if r.get('success') else 'failed', 'query': q})
                if r.get('success'):
                    crawled.extend(r.get('pages', []))
            except Exception as e:
                logger.warning(f'爬虫服务失败，降级DDG: {e}')
                break

        if len(crawled) < enough:  # 降级 DuckDuckGo/SearXNG
            for q in queries:
                if len(crawled) >= enough:
                    break
                try:
                    ddg = await search_web.ainvoke({'query': q, 'max_results': max_results})
                    if isinstance(ddg, list):
                        for it in ddg:
                            if isinstance(it, dict) and it.get('url'):
                                crawled.append({'title': it.get('title', ''), 'url': it.get('url'), 'markdown': it.get('content', '')})
                        tool_calls.append({'tool_name': 'search_web', 'status': 'success', 'query': q})
                except Exception as e:
                    tool_calls.append({'tool_name': 'search_web', 'status': 'failed', 'query': q, 'error': str(e)})

        logger.info(f'爬取完成: {len(crawled)} 个页面')
        return {'crawled_data': crawled, 'tool_calls': tool_calls}
    except Exception as e:
        logger.error(f'数据收集失败: {e}')
        return {'crawled_data': [], 'tool_calls': [{'tool_name': 'crawl', 'status': 'failed', 'error': str(e)}]}


async def search_node(state: AgentState) -> dict:
    """搜索节点：联网搜索 + LLM 接地回答（强制标注来源），无爬取数据时自动补搜"""
    from app.tools.search_tools import search_web

    crawled = state.get('crawled_data', [])
    user_msg = state['user_message']

    if not crawled:
        try:
            current_year = _now_str()[:4]
            kw_msg = await get_chat_model().ainvoke([
                SystemMessage(content=f'根据用户问题生成最有效搜索关键词。规则：优先英文；涉及时效词(最新/现在/版本/latest)加当前年份{current_year}；只返回关键词。'),
                HumanMessage(content=user_msg),
            ])
            keyword = kw_msg.content.strip().strip('"')
            logger.info(f'搜索关键词: {keyword}')
            result = await search_web.ainvoke({'query': keyword, 'max_results': 8})
            if isinstance(result, list):
                for it in result:
                    if isinstance(it, dict) and it.get('url'):
                        crawled.append({'title': it.get('title', ''), 'url': it.get('url'), 'markdown': it.get('content', '')})
        except Exception as e:
            logger.warning(f'联网搜索失败: {e}')

    context = ''
    if crawled:
        parts = []
        for i, page in enumerate(crawled[:10], 1):
            content = (page.get('markdown') or page.get('content') or '')[:3000]
            parts.append(f'--- {page.get("title", "无标题")} ---\n来源: {page.get("url", "")}\n{content}')
        context = '\n\n'.join(parts)

    now_str = _now_str()
    if context:
        prompt = f"""用户请求: {user_msg}

当前时间：{now_str}

以下是实时搜索到的参考内容（可能过时）：
{context}

⚠️ 重要规则：
1. 【时间推理】搜索结果的日期须与当前时间对比，不照搬未来/过去时态。
2. 明显过时的版本号用已知最新信息替代（Claude 最新家族 4.X：Opus 4.8/Sonnet 4.6/Haiku 4.5；GPT-4o/4.1）。
3. 来源直接展示：写"来源：XXX（URL）"，不要用[来源N]隐藏。

当用户要求"找题/搜题/看题"时：返回题目本身（标题/描述/输入输出格式/样例），严格按要求数量返回，不足则基于算法知识补充；不输出解题思路。"""
    else:
        prompt = f"""用户请求: {user_msg}

⚠️ 本次搜索未返回结果。请诚实处理：不编造时效信息；开头标注"以下信息可能不是最新"；基于知识回答。"""

    system_prompt = ('你是严谨的信息检索助手。核心事实优先基于搜索结果并直接展示来源。'
                     '禁止用训练记忆编造时效性信息。')
    try:
        search_model = get_chat_model(temperature=0.7, max_tokens=2048, streaming=True).with_config(tags=['stream_to_user'])
        msg = await search_model.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ])
        reply = _patch_outdated_models((msg.content or '').strip())
        usage = getattr(msg, 'usage_metadata', None) or {}
        return {'agent_name': 'search', 'intent': 'search', 'reply': reply,
                'token_usage': {'input': usage.get('input_tokens', 0), 'output': usage.get('output_tokens', 0)}}
    except Exception as e:
        logger.error(f'Search LLM 失败: {e}')
        if crawled:
            lines = [f'共找到 {len(crawled)} 个结果：\n']
            for i, p in enumerate(crawled[:5], 1):
                lines.append(f'{i}. {p.get("title", "无标题")}\n{p.get("url", "")}\n')
            reply = '\n'.join(lines)
        else:
            reply = f'抱歉，处理失败: {str(e)}'
        return {'agent_name': 'search', 'intent': 'search', 'reply': reply, 'token_usage': {'input': 0, 'output': 0}}


# ===== interim 占位节点（任务10 替换 problem 为子图）=====
async def forum_node(state: AgentState) -> dict:
    """论坛节点：调用 create_react_agent ReAct 发帖（LLM 自主调度工具）"""
    from app.agents.forum import run_forum
    res = await run_forum(state['user_message'], state['user_id'])
    return {'agent_name': 'forum', 'intent': 'forum', **res}


async def problem_node(state: AgentState) -> dict:
    """出题节点：调用 problem StateGraph 子图（gen→verify→submit）"""
    from app.agents.problem import run_problem
    res = await run_problem(state['user_message'], state['user_id'],
                            crawled_data=state.get('crawled_data'), history=state.get('history'))
    return {'agent_name': 'problem', 'intent': 'problem', **res}
