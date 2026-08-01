"""
Forum Agent - 基于 LangGraph create_react_agent 的 ReAct 论坛发帖 Agent

LLM 自主调度工具（搜索/抓取/查板块/发帖/列帖/改帖），最终必须调用 create_post 完成发帖。
取代旧版确定性流水线 execute_forum_task_with_data 与死代码 execute_forum_task。
"""
import logging

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.core.llm import get_chat_model
from app.tools.forum_tools import list_sections, create_post, list_posts, update_post
from app.tools.search_tools import search_web, fetch_url

logger = logging.getLogger(__name__)

FORUM_SYSTEM_PROMPT = """你是Open436平台的论坛内容创作与发布Agent。职责：根据用户需求生成高质量论坛帖子并发布。

工作流程（ReAct，按需调用工具）：
1. 先调用 list_sections 查看可用板块及其 section_id
2. 如需参考资料，调用 search_web 搜索或 fetch_url 抓取指定URL
3. 综合资料创作帖子（标题+正文）
4. 【必须】最后调用 create_post(title, content, section_id, author_id) 发布帖子——这是任务完成的唯一标志，不调用 create_post = 任务失败

帖子质量标准：
- 标题：简洁有吸引力，5-100字符
- 内容：500-5000字，结构清晰，代码可运行有注释
- 原创：综合来源，有自己的分析

⚠️ 格式要求（严格遵守）：
- 禁止使用 # ## ### Markdown标题语法（会打乱排版）
- 用 **加粗** 或 一、二、三 划分层级
- 段落间最多1空行，代码块标注语言
- 结尾加简短总结

author_id：从用户消息末尾的 [系统上下文] 读取，调用 create_post 时必须填入。

板块选择：
- 技术交流：编程技术、开发经验、技术趋势
- 资源分享：工具、教程、开源项目推荐"""


def _build_forum_agent():
    """构建 forum ReAct agent：model 绑 stream_to_user tag（供主图流式直送）"""
    model = get_chat_model(temperature=0.7, max_tokens=4096, streaming=True).with_config(tags=['stream_to_user'])
    tools = [search_web, fetch_url, list_sections, create_post, list_posts, update_post]
    return create_react_agent(model, tools, prompt=FORUM_SYSTEM_PROMPT)


_FORUM_AGENT = None


def get_forum_agent():
    global _FORUM_AGENT
    if _FORUM_AGENT is None:
        _FORUM_AGENT = _build_forum_agent()
    return _FORUM_AGENT


async def run_forum(user_message: str, user_id: int) -> dict:
    """执行 forum ReAct，返回 {reply, tool_calls, token_usage}"""
    content = f'{user_message}\n\n[系统上下文] 当前用户ID: {user_id}。调用 create_post 时 author_id 参数必须填 {user_id}。'
    try:
        result = await get_forum_agent().ainvoke(
            {'messages': [HumanMessage(content=content)]},
            config={'recursion_limit': 30},
        )
        messages = result.get('messages', [])

        # 取最后一条有内容的 AI 消息作为回复
        reply = ''
        for m in reversed(messages):
            if getattr(m, 'type', '') == 'ai' and getattr(m, 'content', None):
                reply = m.content
                break
        if not reply:
            reply = '帖子已发布。'

        # 提取工具调用记录（供 tool_calls 日志）
        tool_calls = []
        for m in messages:
            if getattr(m, 'type', '') == 'ai' and getattr(m, 'tool_calls', None):
                for tc in m.tool_calls:
                    tool_calls.append({'tool_name': tc.get('name', ''), 'status': 'called', 'tool_args': tc.get('args', {})})
            elif getattr(m, 'type', '') == 'tool':
                tool_calls.append({'tool_name': getattr(m, 'name', ''), 'status': 'success'})

        return {'reply': reply, 'tool_calls': tool_calls, 'token_usage': {'input': 0, 'output': 0}}
    except Exception as e:
        logger.error(f'Forum ReAct 异常: {e}', exc_info=True)
        return {'reply': f'论坛Agent执行异常: {str(e)}', 'tool_calls': [], 'token_usage': {'input': 0, 'output': 0}}
