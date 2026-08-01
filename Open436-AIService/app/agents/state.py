"""
Agent 状态定义
"""
from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    user_message: str
    user_id: int
    history: list[dict]
    crawled_data: list
    tool_calls: list[dict]
    step_results: list[dict]
    total_tokens: dict
    plan: Optional[dict]
    steps: list[dict]
    understanding: str
    step_index: int
    reply: str
    agent_name: str
    intent: str
    token_usage: dict
