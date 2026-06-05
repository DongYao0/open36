"""
LangGraph状态图 - 多Agent路由与执行
"""
import logging
from typing import TypedDict, Any

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


async def unclear_node(state: AgentState) -> AgentState:
    """澄清节点"""
    state['agent_name'] = 'router'
    state['reply'] = (
        '抱歉，我没有完全理解您的指令。您是想要：\n'
        '1. 在论坛发布一篇帖子\n'
        '2. 生成一道算法题目\n'
        '请告诉我您的具体需求。'
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
    else:
        state = await unclear_node(state)

    return {
        'reply': state['reply'],
        'intent': state['intent'],
        'agent_name': state['agent_name'],
        'tool_calls': state['tool_calls'],
        'token_usage': state['token_usage'],
    }
