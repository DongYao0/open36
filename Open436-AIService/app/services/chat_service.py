"""
对话业务逻辑服务
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.tool_call import ToolCall
from app.agents.graph import run_agent

logger = logging.getLogger(__name__)


async def process_chat(message: str, user_id: int, conversation_id: str = None) -> dict:
    """
    处理对话请求

    Args:
        message: 用户消息
        user_id: 管理员ID
        conversation_id: 会话ID（可选）

    Returns:
        ChatResponse格式的字典
    """
    async with async_session() as session:
        # 1. 获取或创建会话
        if conversation_id:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise ValueError('会话不存在')
        else:
            conversation = Conversation(
                user_id=user_id,
                title=message[:50],  # 自动从首条消息提取标题
            )
            session.add(conversation)
            await session.flush()
            conversation_id = str(conversation.id)

        # 2. 保存用户消息
        user_msg = Message(
            conversation_id=conversation.id,
            role='user',
            content=message,
        )
        session.add(user_msg)
        await session.flush()

        # 3. 调用Agent执行
        agent_result = await run_agent(message, user_id)

        # 4. 保存Agent回复
        assistant_msg = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=agent_result['reply'],
            intent=agent_result['intent'],
            agent_name=agent_result['agent_name'],
            token_usage=agent_result['token_usage'],
        )
        session.add(assistant_msg)
        await session.flush()

        # 5. 保存工具调用记录
        for tc in agent_result.get('tool_calls', []):
            tool_call = ToolCall(
                message_id=assistant_msg.id,
                tool_name=tc.get('tool_name', ''),
                tool_input=tc.get('tool_args', {}),
                tool_output=tc.get('result_summary'),
                status=tc.get('status', 'pending'),
                error_message=tc.get('error'),
                duration_ms=tc.get('duration_ms'),
            )
            session.add(tool_call)

        # 6. 更新会话时间
        conversation.updated_at = datetime.utcnow()

        await session.commit()

        return {
            'conversation_id': conversation_id,
            'message_id': str(assistant_msg.id),
            'reply': agent_result['reply'],
            'intent': agent_result['intent'],
            'agent_name': agent_result['agent_name'],
            'tool_calls': agent_result.get('tool_calls', []),
            'token_usage': agent_result['token_usage'],
        }
