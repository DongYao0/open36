"""
对话接口 - 支持同步/流式/停止
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.dependencies import get_current_admin
from app.schemas.chat import ChatRequest, StopRequest
from app.core.responses import success_response, error_response
from app.services.chat_service import process_chat, process_chat_stream, stop_chat

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/chat')
async def chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_admin),
):
    """同步对话接口 - 等待Agent执行完成返回结果"""
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


@router.post('/chat/stream')
async def chat_stream(
    request: ChatRequest,
    user_id: int = Depends(get_current_admin),
):
    """流式对话接口 - SSE 逐字输出"""

    async def event_generator():
        try:
            async for chunk in process_chat_stream(
                message=request.message,
                user_id=user_id,
                conversation_id=request.conversation_id,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f'流式生成器异常: {e}', exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@router.post('/chat/stop')
async def chat_stop(
    request: StopRequest,
    user_id: int = Depends(get_current_admin),
):
    """停止正在进行的流式对话"""
    stopped = stop_chat(request.conversation_id)
    if stopped:
        return JSONResponse(content=success_response(message='已停止生成'))
    else:
        return JSONResponse(content=error_response('无活跃任务', code=40402, status_code=404))
