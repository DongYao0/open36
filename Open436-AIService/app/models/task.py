"""
异步任务模型 - ai_tasks表
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class Task(Base):
    __tablename__ = 'ai_tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(BigInteger, nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('ai_conversations.id', ondelete='SET NULL'), nullable=True)
    task_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='pending', index=True)
    input_data = Column(JSONB, nullable=False)
    result_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    agent_name = Column(String(50), nullable=False)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
