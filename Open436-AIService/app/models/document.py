"""
文档元数据模型 - ai_documents表
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Document(Base):
    __tablename__ = 'ai_documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(BigInteger, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    chunk_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending/processing/completed/failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
