"""
LangGraph状态图 - 多Agent路由与执行
"""
import logging
from typing import TypedDict, Any

import httpx

from app.config import settings
from app.agents.router import classify_intent
from app.agents.forum import execute_forum_task
from app.agents.problem import execute_problem_task

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Agent状态"""
    user_message: str
    user_id: int
    intent: str
    agent_name: str
    reply: str
    tool_calls: list[dict]
    token_usage: dict


async def route_node(state: AgentState) -> AgentState:
    """路由节点：意图分类"""
    result = await classify_intent(state['user_message'])
    state['intent'] = result['intent']
    state['agent_name'] = 'router'
    logger.info(f'意图分类结果: {result}')
    return state


async def forum_node(state: AgentState) -> AgentState:
    """论坛Agent节点"""
    result = await execute_forum_task(state['user_message'], state['user_id'])
    state['agent_name'] = 'forum'
    state['reply'] = result['reply']
    state['tool_calls'] = result['tool_calls']
    state['token_usage'] = result['token_usage']
    return state


async def problem_node(state: AgentState) -> AgentState:
    """出题Agent节点"""
    result = await execute_problem_task(state['user_message'], state['user_id'])
    state['agent_name'] = 'problem'
    state['reply'] = result['reply']
    state['tool_calls'] = result['tool_calls']
    state['token_usage'] = result['token_usage']
    return state


async def query_node(state: AgentState) -> AgentState:
    """查询节点：主Agent直接处理简单查询"""
    state['agent_name'] = 'router'
    state['reply'] = f'收到您的查询："{state["user_message"]}"。查询功能正在完善中。'
    state['tool_calls'] = []
    state['token_usage'] = {'input': 0, 'output': 0}
    return state


CHAT_SYSTEM_PROMPT = """你是Open436平台的AI助手，名叫小46。你性格友好、专业、简洁。
- 可以回答日常问题、闲聊、提供帮助
- 涉及平台操作时，可以引导用户使用具体功能（发帖、出题等）
- 回复简洁自然，不要过度使用markdown格式"""


async def chat_node(state: AgentState) -> AgentState:
    """通用聊天节点：使用LLM直接对话"""
    try:
        base_url = settings.LLM_BASE_URL or 'https://api.deepseek.com'
        url = f'{base_url}/v1/chat/completions'

        payload = {
            'model': settings.LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': CHAT_SYSTEM_PROMPT},
                {'role': 'user', 'content': state['user_message']},
            ],
            'temperature': 0.7,
            'max_tokens': 1024,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json=payload,
                headers={'Authorization': f'Bearer {settings.ANTHROPIC_API_KEY}'},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()

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


async def unclear_node(state: AgentState) -> AgentState:
    """澄清节点"""
    state['agent_name'] = 'router'
    state['reply'] = (
        '抱歉，我没有完全理解您的指令。您可以：\n'
        '- 直接描述需求，例如"帮我发一篇帖子"或"生成一道算法题"\n'
        '- 或者直接和我聊天也可以哦'
    )
    state['tool_calls'] = []
    state['token_usage'] = {'input': 0, 'output': 0}
    return state


async def run_agent(user_message: str, user_id: int) -> dict:
    """
    执行Agent工作流

    Args:
        user_message: 用户消息
        user_id: 当前管理员ID

    Returns:
        {"reply": "...", "intent": "...", "agent_name": "...", "tool_calls": [...], "token_usage": {...}}
    """
    state: AgentState = {
        'user_message': user_message,
        'user_id': user_id,
        'intent': '',
        'agent_name': '',
        'reply': '',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }

    # Step 1: 意图分类
    state = await route_node(state)

    # Step 2: 根据意图路由到对应Agent
    intent = state['intent']
    if intent == 'forum':
        state = await forum_node(state)
    elif intent == 'problem':
        state = await problem_node(state)
    elif intent == 'query':
        state = await query_node(state)
    elif intent == 'chat':
        state = await chat_node(state)
    else:
        state = await unclear_node(state)

    return {
        'reply': state['reply'],
        'intent': state['intent'],
        'agent_name': state['agent_name'],
        'tool_calls': state['tool_calls'],
        'token_usage': state['token_usage'],
    }
