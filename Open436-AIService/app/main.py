"""
M8 AI智能服务 - FastAPI入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.database import init_db, close_db
from app.models import *  # noqa: F401,F403 — 确保所有模型注册到 Base.metadata
from app.core.redis import init_redis, close_redis
from app.core.responses import success_response, error_response
from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.agents import router as agents_router

logging.basicConfig(
    level=getattr(logging, settings.APP_LOG_LEVEL.upper(), logging.INFO),
    format='[%(levelname)s] %(asctime)s %(module)s %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info('AI服务启动中...')
    await init_db()
    await init_redis()
    logger.info('AI服务启动完成')
    yield
    await close_db()
    await close_redis()
    logger.info('AI服务已关闭')


app = FastAPI(
    title='Open436 AI智能服务',
    description='M8 AI智能服务 - 多Agent驱动的平台运营能力',
    version='1.0.0',
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 注册路由
app.include_router(chat_router, prefix='/api/ai', tags=['AI对话'])
app.include_router(conversations_router, prefix='/api/ai', tags=['会话管理'])
app.include_router(agents_router, prefix='/api/ai', tags=['Agent管理'])


@app.get('/health')
async def health_check():
    """健康检查"""
    return success_response(data={
        'status': 'healthy',
        'service': 'ai-service',
        'version': '1.0.0',
    })


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f'未处理的异常: {exc}', exc_info=True)
    resp = error_response(
        message='服务器内部错误',
        code=500,
        status_code=500
    )
    return JSONResponse(content=resp[0], status_code=resp[1])
