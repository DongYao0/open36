"""
会话管理接口
"""
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, func

from app.dependencies import get_current_admin
from app.core.database import async_session
from app.core.responses import success_response, error_response
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/conversations')
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user_id: int = Depends(get_current_admin),
):
    """查询当前用户的会话列表"""
    async with async_session() as session:
        # 查询总数
        count_result = await session.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        total = count_result.scalar()

        # 查询列表
        offset = (page - 1) * page_size
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        conversations = result.scalars().all()

        results = []
        for conv in conversations:
            # 查询消息数
            msg_count_result = await session.execute(
                select(func.count(Message.id)).where(Message.conversation_id == conv.id)
            )
            msg_count = msg_count_result.scalar()

            results.append({
                'conversation_id': str(conv.id),
                'title': conv.title,
                'status': conv.status,
                'message_count': msg_count,
                'last_message_at': conv.updated_at.isoformat() if conv.updated_at else None,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
            })

        return JSONResponse(content=success_response(data={
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': results,
        }))


@router.get('/conversations/{conversation_id}')
async def get_conversation(
    conversation_id: str,
    user_id: int = Depends(get_current_admin),
):
    """查询会话详情（含消息历史）"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            resp, code = error_response('会话不存在', code=40401, status_code=404)
            return JSONResponse(content=resp, status_code=code)

        # 查询消息
        msg_result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()

        return JSONResponse(content=success_response(data={
            'conversation_id': str(conv.id),
            'title': conv.title,
            'status': conv.status,
            'created_at': conv.created_at.isoformat() if conv.created_at else None,
            'messages': [
                {
                    'message_id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'intent': msg.intent,
                    'agent_name': msg.agent_name,
                    'token_usage': msg.token_usage,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in messages
            ],
        }))


@router.delete('/conversations/{conversation_id}')
async def delete_conversation(
    conversation_id: str,
    user_id: int = Depends(get_current_admin),
):
    """删除会话及其所有消息"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            resp, code = error_response('会话不存在', code=40401, status_code=404)
            return JSONResponse(content=resp, status_code=code)

        await session.delete(conv)
        await session.commit()

        return JSONResponse(content=success_response(message='会话已删除'))
