"""
工具调用记录模型 - ai_tool_calls表
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class ToolCall(Base):
    __tablename__ = 'ai_tool_calls'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('ai_messages.id', ondelete='CASCADE'), nullable=True, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey('ai_tasks.id', ondelete='CASCADE'), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False)
    tool_input = Column(JSONB, nullable=False)
    tool_output = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # pending/success/failed
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
