"""
统一 LLM 客户端 - 替代散落在各 agent 中的 _call_llm
支持同步调用和流式调用（SSE）
"""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_BASE_URL = 'https://api.deepseek.com'
DEFAULT_TIMEOUT = 60.0


class LLMClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(self):
        self._base_url = None

    @property
    def base_url(self) -> str:
        if self._base_url is None:
            self._base_url = settings.LLM_BASE_URL or DEFAULT_BASE_URL
        return self._base_url

    @property
    def api_key(self) -> str:
        return settings.ANTHROPIC_API_KEY

    @property
    def model(self) -> str:
        return settings.LLM_MODEL

    def _headers(self) -> dict:
        return {'Authorization': f'Bearer {self.api_key}'}

    def _build_payload(
        self,
        messages: list,
        tools: list = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> dict:
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream,
        }
        if tools:
            payload['tools'] = tools
        return payload

    async def chat(
        self,
        messages: list,
        tools: list = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict:
        """同步调用 - 返回完整响应"""
        url = f'{self.base_url}/v1/chat/completions'
        payload = self._build_payload(
            messages=messages, tools=tools,
            temperature=temperature, max_tokens=max_tokens,
        )

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, json=payload,
                headers=self._headers(),
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()

    async def chat_stream(
        self,
        messages: list,
        tools: list = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """流式调用 - yield 每个 delta chunk

        Yields:
            dict: OpenAI delta 对象，如 {'content': '你好'} 或 {'tool_calls': [...]}
        """
        url = f'{self.base_url}/v1/chat/completions'
        payload = self._build_payload(
            messages=messages, tools=tools,
            temperature=temperature, max_tokens=max_tokens,
            stream=True,
        )

        async with httpx.AsyncClient() as client:
            async with client.stream(
                'POST', url, json=payload,
                headers=self._headers(),
                timeout=timeout,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith('data: '):
                        continue
                    data_str = line[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get('choices', [{}])[0].get('delta', {})
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue


# 全局单例
llm = LLMClient()
