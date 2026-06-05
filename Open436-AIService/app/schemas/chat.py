"""
对话请求/响应Schema
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=5000, description='用户消息')
    conversation_id: str | None = Field(None, description='会话ID，不传则新建')


class ChatResponse(BaseModel):
    """对话响应"""
    conversation_id: str
    message_id: str
    reply: str
    intent: str
    agent_name: str
    tool_calls: list[dict]
    token_usage: dict
