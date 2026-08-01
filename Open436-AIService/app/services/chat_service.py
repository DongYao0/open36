"""
对话业务逻辑服务 - 支持同步/流式/停止
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.tool_call import ToolCall
from app.agents.graph import run_agent, run_agent_stream

logger = logging.getLogger(__name__)

# 活跃的流式任务 {conversation_id: asyncio.Task}
_active_streams: dict[str, asyncio.Task] = {}


async def _get_or_create_conversation(
    session: AsyncSession, user_id: int, conversation_id: str = None, first_message: str = ''
) -> Conversation:
    """获取或创建会话"""
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
            title=first_message[:50],
        )
        session.add(conversation)
        await session.flush()
    return conversation


async def _load_history(session: AsyncSession, conversation_id, limit: int = 20) -> list[dict]:
    """加载历史消息作为 LLM 上下文"""
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.role.in_(['user', 'assistant']))
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages = list(reversed(result.scalars().all()))
    return [{'role': msg.role, 'content': msg.content} for msg in messages]


async def process_chat(message: str, user_id: int, conversation_id: str = None) -> dict:
    """同步对话处理"""
    async with async_session() as session:
        # 1. 获取或创建会话
        conversation = await _get_or_create_conversation(session, user_id, conversation_id, message)
        conversation_id = str(conversation.id)

        # 2. 保存用户消息
        user_msg = Message(
            conversation_id=conversation.id,
            role='user',
            content=message,
        )
        session.add(user_msg)
        await session.flush()

        # 3. 加载历史消息（排除刚保存的这条）
        history = await _load_history(session, conversation.id, limit=20)
        # 去掉最后一条（就是刚存的用户消息，避免重复）
        if history and history[-1]['content'] == message:
            history = history[:-1]

        # 4. 调用Agent执行（传入历史）
        agent_result = await run_agent(message, user_id, history=history)

        # 5. 保存Agent回复
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

        # 6. 保存工具调用记录
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

        # 7. 更新会话时间
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


async def process_chat_stream(message: str, user_id: int, conversation_id: str = None):
    """流式对话处理 - yield SSE chunk

    Yields:
        dict: {'type': 'content'|'meta'|'done'|'stopped'|'error', ...}
    """
    full_reply = ''
    conversation = None
    assistant_msg = None

    try:
        async with async_session() as session:
            # 1. 获取或创建会话
            conversation = await _get_or_create_conversation(session, user_id, conversation_id, message)
            conversation_id = str(conversation.id)

            # 2. 保存用户消息
            user_msg = Message(
                conversation_id=conversation.id,
                role='user',
                content=message,
            )
            session.add(user_msg)
            await session.flush()

            # 3. 加载历史
            history = await _load_history(session, conversation.id, limit=20)
            if history and history[-1]['content'] == message:
                history = history[:-1]

            # 先提交用户消息和会话
            await session.commit()

        # 4. 注册活跃任务
        task = asyncio.current_task()
        _active_streams[conversation_id] = task

        # 5. 流式调用 Agent
        agent_name = 'chat'
        intent = 'chat'
        tool_calls = []
        token_usage = {'input': 0, 'output': 0}

        async for chunk in run_agent_stream(message, user_id, history=history):
            if chunk['type'] == 'content':
                full_reply += chunk['content']
                yield chunk
            elif chunk['type'] == 'meta':
                intent = chunk.get('intent', intent)
                # 注入 conversation_id 到 meta 事件，前端需要它来调用 stop 接口
                chunk['conversation_id'] = conversation_id
                yield chunk
            elif chunk['type'] == 'done':
                agent_name = chunk.get('agent_name', agent_name)
                tool_calls = chunk.get('tool_calls', tool_calls)
                token_usage = chunk.get('token_usage', token_usage)

        # 6. 流结束后保存到数据库
        async with async_session() as session:
            assistant_msg = Message(
                conversation_id=uuid.UUID(conversation_id),
                role='assistant',
                content=full_reply,
                intent=intent,
                agent_name=agent_name,
                token_usage=token_usage,
            )
            session.add(assistant_msg)
            await session.flush()

            for tc in tool_calls:
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

            # 更新会话时间
            result = await session.execute(
                select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
            )
            conv = result.scalar_one_or_none()
            if conv:
                conv.updated_at = datetime.utcnow()

            await session.commit()

        yield {
            'type': 'done',
            'conversation_id': conversation_id,
            'message_id': str(assistant_msg.id),
            'intent': intent,
            'agent_name': agent_name,
            'tool_calls': tool_calls,
            'token_usage': token_usage,
        }

    except asyncio.CancelledError:
        logger.info(f'流式对话被取消: conversation_id={conversation_id}')
        # 保存已生成的部分内容
        if full_reply and conversation_id:
            try:
                async with async_session() as session:
                    msg = Message(
                        conversation_id=uuid.UUID(conversation_id),
                        role='assistant',
                        content=full_reply + '\n\n_[已停止生成]_',
                        intent=intent if 'intent' in dir() else 'chat',
                        agent_name=agent_name if 'agent_name' in dir() else 'chat',
                    )
                    session.add(msg)
                    await session.commit()
            except Exception as e:
                logger.error(f'保存中断消息失败: {e}')
        yield {'type': 'stopped', 'content': full_reply}

    except Exception as e:
        logger.error(f'流式对话异常: {e}', exc_info=True)
        yield {'type': 'error', 'message': str(e)}

    finally:
        _active_streams.pop(conversation_id, None)


def stop_chat(conversation_id: str) -> bool:
    """停止指定会话的活跃流式任务"""
    task = _active_streams.get(conversation_id)
    if task and not task.done():
        task.cancel()
        return True
    return False
