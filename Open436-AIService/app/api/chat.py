"""
同步对话接口
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.dependencies import get_current_admin
from app.schemas.chat import ChatRequest
from app.core.responses import success_response, error_response
from app.services.chat_service import process_chat

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/chat')
async def chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_admin),
):
    """
    同步对话接口

    发送消息并等待Agent执行完成返回结果。
    """
    try:
        result = await process_chat(
            message=request.message,
            user_id=user_id,
            conversation_id=request.conversation_id,
        )
        return JSONResponse(content=success_response(data=result))
    except ValueError as e:
        resp, code = error_response(str(e), code=40401, status_code=404)
        return JSONResponse(content=resp, status_code=code)
    except Exception as e:
        logger.error(f'对话处理异常: {e}', exc_info=True)
        resp, code = error_response(
            'Agent执行异常', code=50001, status_code=500
        )
        return JSONResponse(content=resp, status_code=code)
