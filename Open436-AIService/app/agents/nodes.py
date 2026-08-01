"""
Agent 节点占位实现 - 让 AI Service 能够启动
"""
import logging

logger = logging.getLogger(__name__)


def _patch_outdated_models(text: str) -> str:
    return text


async def chat_node(state: dict) -> dict:
    return {
        'reply': state.get('user_message', ''),
        'agent_name': 'chat',
        'intent': 'chat',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }


async def crawl_node(state: dict) -> dict:
    return {
        'reply': '爬取结果占位',
        'agent_name': 'crawl',
        'intent': 'crawl',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }


async def search_node(state: dict) -> dict:
    return {
        'reply': '搜索结果占位',
        'agent_name': 'search',
        'intent': 'search',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }


async def query_node(state: dict) -> dict:
    return {
        'reply': '查询结果占位',
        'agent_name': 'query',
        'intent': 'query',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }


async def unclear_node(state: dict) -> dict:
    return {
        'reply': '我不太理解你的问题，请再描述一下。',
        'agent_name': 'unclear',
        'intent': 'unclear',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }


async def forum_node(state: dict) -> dict:
    return {
        'reply': '论坛操作占位',
        'agent_name': 'forum',
        'intent': 'forum',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }


async def problem_node(state: dict) -> dict:
    return {
        'reply': '题目生成占位',
        'agent_name': 'problem',
        'intent': 'problem',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }
