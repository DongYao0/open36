"""
Agent配置模型 - ai_agent_configs表
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class AgentConfig(Base):
    __tablename__ = 'ai_agent_configs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    temperature = Column(Numeric(3, 2), nullable=False, default=0.70)
    max_tokens = Column(Integer, nullable=False, default=4096)
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
