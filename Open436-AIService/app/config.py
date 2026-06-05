"""
配置管理（pydantic-settings）
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = 'postgresql://open436:open436@localhost:55432/ai_db'

    # Redis（DB 2，避免与Sa-Token默认DB 0冲突）
    REDIS_URL: str = 'redis://localhost:6379/2'

    # Milvus向量数据库
    MILVUS_HOST: str = 'localhost'
    MILVUS_PORT: int = 19530

    # LLM
    ANTHROPIC_API_KEY: str = ''
    LLM_BASE_URL: str = ''  # DeepSeek/OpenAI兼容API的base_url
    LLM_MODEL: str = 'deepseek-chat'  # 默认模型

    # 联网搜索（Tavily）
    TAVILY_API_KEY: str = ''

    # 内部服务地址
    CONTENT_SERVICE_URL: str = 'http://localhost:8003'
    SECTION_SERVICE_URL: str = 'http://localhost:8005'
    USER_SERVICE_URL: str = 'http://localhost:8002'
    HOJ_API_URL: str = 'http://localhost:6688'

    # HOJ管理员账号
    HOJ_ADMIN_USER: str = 'admin'
    HOJ_ADMIN_PASS: str = 'admin123'

    # 内部API密钥
    INTERNAL_API_KEY: str = 'open436-internal-secret'

    # Consul
    CONSUL_URL: str = 'http://localhost:8500'
    CONSUL_SERVICE_NAME: str = 'ai-service'
    SERVICE_PORT: int = 8008

    # 应用配置
    APP_DEBUG: bool = True
    APP_LOG_LEVEL: str = 'info'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
