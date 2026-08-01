"""
Agent管理接口
"""
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.dependencies import get_current_admin
from app.core.database import async_session
from app.core.responses import success_response, error_response
from app.models.agent_config import AgentConfig

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/agents')
async def list_agents(
    user_id: int = Depends(get_current_admin),
):
    """查询所有Agent配置"""
    async with async_session() as session:
        result = await session.execute(select(AgentConfig).order_by(AgentConfig.agent_name))
        agents = result.scalars().all()

        return JSONResponse(content=success_response(data=[
            {
                'agent_name': a.agent_name,
                'display_name': a.display_name,
                'model': a.model,
                'temperature': float(a.temperature),
                'max_tokens': a.max_tokens,
                'is_enabled': a.is_enabled,
            }
            for a in agents
        ]))


@router.put('/agents/{agent_name}')
async def update_agent(
    agent_name: str,
    request: dict,
    user_id: int = Depends(get_current_admin),
):
    """更新Agent配置"""
    async with async_session() as session:
        result = await session.execute(
            select(AgentConfig).where(AgentConfig.agent_name == agent_name)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            resp, code = error_response('Agent不存在', code=40402, status_code=404)
            return JSONResponse(content=resp, status_code=code)

        # 更新允许的字段
        if 'temperature' in request:
            agent.temperature = request['temperature']
        if 'max_tokens' in request:
            agent.max_tokens = request['max_tokens']
        if 'is_enabled' in request:
            agent.is_enabled = request['is_enabled']
        if 'system_prompt' in request:
            agent.system_prompt = request['system_prompt']

        await session.commit()

        return JSONResponse(content=success_response(
            data={
                'agent_name': agent.agent_name,
                'display_name': agent.display_name,
                'model': agent.model,
                'temperature': float(agent.temperature),
                'max_tokens': agent.max_tokens,
                'is_enabled': agent.is_enabled,
            },
            message='Agent配置已更新',
        ))
