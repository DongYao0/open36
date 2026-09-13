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
3. 综合资料创作帖子（标题+摘要+正文；资源帖另含资源链接）
4. 【必须】最后调用 create_post(title, summary, content, section_id, author_id, resource_url) 发布帖子——这是任务完成的唯一标志，不调用 create_post = 任务失败

帖子质量标准：
- 标题：简洁有吸引力，5-100字符
- 摘要：20-300字符，单独概括读者能获得什么，用于列表卡片，不能与正文混写
- 正文：500-5000字，结构清晰，代码可运行有注释
- 原创：综合来源，有自己的分析

⚠️ 格式要求（严格遵守）：
- 禁止使用 # ## ### Markdown标题语法（会打乱排版）
- 用 **加粗** 或 一、二、三 划分层级
- 段落间最多1空行，代码块标注语言
- 结尾加简短总结

author_id：从用户消息末尾的 [系统上下文] 读取，调用 create_post 时必须填入。

板块选择与发布结构：
- 技术交流：编程技术、开发经验、技术趋势。调用 create_post 时传 title、summary、content，不传 resource_url。
- 资源分享：工具、教程、开源项目推荐。必须提供可直接使用的官网、GitHub、下载或网盘地址到 resource_url；content 只写资源用途、适用人群、上手步骤和注意事项，工具会自动把链接写成详情页的“访问资源”入口。
- 发布前确认 section_id 对应目标板块；不要把摘要、链接字段遗漏或塞进标题。"""


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
    """兼容入口；新工作流由 run_forum_draft 承担。"""
    from app.agents.forum_draft import run_forum_draft
    try:
        return await run_forum_draft(user_message, user_id, [])
    except Exception as e:
        logger.error(f'论坛草稿生成异常: {e}', exc_info=True)
        return {'reply': f'论坛草稿生成异常: {str(e)}', 'tool_calls': [],
                'token_usage': {'input': 0, 'output': 0}}
