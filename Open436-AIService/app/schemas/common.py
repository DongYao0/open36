"""
通用响应Schema
"""
from pydantic import BaseModel
from typing import Any


class PaginatedResponse(BaseModel):
    """分页响应"""
    count: int
    page: int
    page_size: int
    results: list[Any]
