"""
FastAPI依赖注入
"""
from fastapi import Header, HTTPException


async def get_current_admin(
    x_user_id: str = Header(alias='X-User-Id'),
    x_user_role: str = Header(alias='X-User-Role'),
) -> int:
    """从Kong注入的Header中获取当前管理员信息"""
    if x_user_role != 'admin':
        raise HTTPException(status_code=403, detail='权限不足：仅管理员可访问')
    return int(x_user_id)
