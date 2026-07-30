"""
统一 LLM 入口 - LangChain ChatOpenAI 工厂（对接 OpenAI 兼容端点，默认 DeepSeek）

供 LangGraph StateGraph 节点与 create_react_agent 使用，替代散落各处的 _call_llm。
旧版 httpx LLMClient 已随全量迁移移除（所有调用方改用 get_chat_model）。
"""
from langchain_openai import ChatOpenAI

from app.config import settings

# 默认配置
DEFAULT_BASE_URL = 'https://api.deepseek.com'
DEFAULT_TIMEOUT = 60.0


def get_chat_model(
    temperature: float = 0.3,
    max_tokens: int = 1024,
    streaming: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> ChatOpenAI:
    """构建 ChatOpenAI 实例（LangGraph/LangChain 统一 LLM 入口）"""
    return ChatOpenAI(
        base_url=settings.LLM_BASE_URL or DEFAULT_BASE_URL,
        model=settings.LLM_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
        timeout=timeout,
    )
