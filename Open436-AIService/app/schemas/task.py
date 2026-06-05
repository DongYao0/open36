"""
任务请求/响应Schema
"""
from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    """创建异步任务请求"""
    task_type: str = Field(..., description='任务类型: single_post/batch_post/single_problem/batch_problem')
    input_data: dict = Field(..., description='任务输入参数')
    conversation_id: str | None = Field(None, description='关联会话ID')


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    task_type: str
    status: str
    agent_name: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
