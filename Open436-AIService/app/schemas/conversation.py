"""
会话响应Schema
"""
from pydantic import BaseModel


class ConversationResponse(BaseModel):
    """会话响应"""
    conversation_id: str
    title: str
    status: str
    message_count: int = 0
    last_message_at: str | None = None
    created_at: str
