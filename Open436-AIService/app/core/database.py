"""
SQLAlchemy异步数据库引擎
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 将 postgresql:// 替换为 postgresql+psycopg://
db_url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://')

engine = create_async_engine(
    db_url,
    echo=settings.APP_DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # 用前检测连接是否存活
    pool_recycle=1800,    # 连接最多复用30分钟
    pool_timeout=30,      # 获取连接超时30秒
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库连接"""
    pass


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
