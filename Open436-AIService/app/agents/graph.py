"""
LangGraph 主图编排 - StateGraph 实现（取代旧版手写 for 循环）

主图：START → orchestrator(规划) → route(条件边) → {chat|search|forum|problem|query|unclear} → patch → END
- 多步（任务7）：route 多步时进入 exec_step 自循环（当前 interim 退化为首步）。
- 流式（任务8）：run_agent_stream 当前为 interim 假流式，将改为 astream_events 真流式。
对外契约：run_agent / run_agent_stream 签名与返回结构与旧版一致，chat_service 无感。
"""
import logging

from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.router import orchestrate
from app.agents.nodes import (
    chat_node, crawl_node, search_node, query_node, unclear_node,
    forum_node, problem_node, _patch_outdated_models,
)

logger = logging.getLogger(__name__)

# 单步 agent → 节点名映射
_AGENT_TO_NODE = {
    'chat': 'chat', 'search': 'search', 'forum': 'forum',
    'problem': 'problem', 'query': 'query', 'unclear': 'unclear',
}


async def orchestrator_node(state: AgentState) -> dict:
    """规划节点：理解意图 + 产出 steps"""
    plan = await orchestrate(state['user_message'])
    steps = plan.get('steps') or [
        {'step': 1, 'agent': 'unclear', 'task': state['user_message'], 'input': state['user_message']}
    ]
    logger.info(f'Orchestrator 规划: {plan.get("understanding")} → {len(steps)} 步')
    return {'plan': plan, 'steps': steps, 'understanding': plan.get('understanding', ''), 'step_index': 0}


def route_after_plan(state: AgentState) -> str:
    """条件边：单步直接路由；多步进入 exec_step 串行循环"""
    steps = state.get('steps', [])
    if len(steps) <= 1:
        agent = steps[0].get('agent', 'chat') if steps else 'unclear'
        return _AGENT_TO_NODE.get(agent, 'unclear')
    return 'exec_step'


async def patch_node(state: AgentState) -> dict:
    """终节点：后处理过时版本号"""
    return {'reply': _patch_outdated_models(state.get('reply', ''))}


# step.agent → 节点函数
_AGENT_NODE_MAP = {
    'chat': chat_node, 'search': search_node, 'forum': forum_node,
    'problem': problem_node, 'query': query_node, 'unclear': unclear_node,
}


async def exec_step(state: AgentState) -> dict:
    """多步串行执行当前 step_index 指向的步骤，注入前序结果，推进指针"""
    idx = state.get('step_index', 0)
    steps = state.get('steps', [])
    if idx >= len(steps):
        return {}

    step = steps[idx]
    agent = step.get('agent', 'chat')
    step_input = step.get('input') or step.get('task', '') or state['user_message']

    # 前序步骤结果注入（复刻 legacy graph.py:722-727）
    for i, prev in enumerate(state.get('step_results', [])):
        if f'step {i + 1}' in step_input.lower() or f'步骤{i + 1}' in step_input:
            step_input = f'{step_input}\n\n前序步骤结果:\n{(prev.get("reply") or "")[:2000]}'

    sub_state = {**state, 'user_message': step_input}
    node_fn = _AGENT_NODE_MAP.get(agent, unclear_node)
    res = await node_fn(sub_state)

    prev_tok = state.get('token_usage') or {'input': 0, 'output': 0}
    st = res.get('token_usage') or {'input': 0, 'output': 0}
    return {
        'step_results': [{'step_index': idx, 'agent': agent, 'reply': res.get('reply', ''),
                          'token_usage': st}],
        'tool_calls': res.get('tool_calls', []),
        'reply': res.get('reply', ''),
        'agent_name': res.get('agent_name', agent),
        'intent': res.get('intent', agent),
        'step_index': idx + 1,
        'token_usage': {'input': prev_tok.get('input', 0) + st.get('input', 0),
                        'output': prev_tok.get('output', 0) + st.get('output', 0)},
    }


def route_after_exec(state: AgentState) -> str:
    """多步循环条件：仍有未执行步骤则继续循环，否则进 patch"""
    if state.get('step_index', 0) < len(state.get('steps', [])):
        return 'exec_step'
    return 'patch'


def build_graph():
    """构建并编译主 StateGraph"""
    g = StateGraph(AgentState)
    g.add_node('orchestrator', orchestrator_node)
    g.add_node('exec_step', exec_step)
    g.add_node('chat', chat_node)
    g.add_node('search', search_node)
    g.add_node('forum', forum_node)
    g.add_node('problem', problem_node)
    g.add_node('query', query_node)
    g.add_node('unclear', unclear_node)
    g.add_node('patch', patch_node)

    g.add_edge(START, 'orchestrator')
    g.add_conditional_edges('orchestrator', route_after_plan, {
        'chat': 'chat', 'search': 'search', 'forum': 'forum', 'problem': 'problem',
        'query': 'query', 'unclear': 'unclear', 'exec_step': 'exec_step',
    })
    # 单步 agent 直达 patch
    for n in ('chat', 'search', 'forum', 'problem', 'query', 'unclear'):
        g.add_edge(n, 'patch')
    # 多步 exec_step 自循环
    g.add_conditional_edges('exec_step', route_after_exec, {'exec_step': 'exec_step', 'patch': 'patch'})
    g.add_edge('patch', END)
    return g.compile()


_GRAPH = None


def _get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


async def run_agent(user_message: str, user_id: int, history: list[dict] = None) -> dict:
    """同步执行 Agent 工作流（StateGraph）。签名/返回结构与旧版对齐。"""
    init_state: AgentState = {
        'user_message': user_message,
        'user_id': user_id,
        'history': history or [],
        'crawled_data': [],
        'tool_calls': [],
        'step_results': [],
        'total_tokens': {'input': 0, 'output': 0},
    }
    try:
        final = await _get_graph().ainvoke(init_state, config={'recursion_limit': 50})
    except Exception as e:
        logger.error(f'Agent 工作流异常: {e}', exc_info=True)
        return {'reply': f'抱歉，处理失败: {str(e)}', 'intent': 'chat', 'agent_name': 'chat',
                'tool_calls': [], 'token_usage': {'input': 0, 'output': 0}}

    steps = final.get('steps', [])
    return {
        'reply': final.get('reply', ''),
        'intent': final.get('intent') or (steps[-1].get('agent', 'chat') if steps else 'chat'),
        'agent_name': final.get('agent_name', 'chat'),
        'tool_calls': final.get('tool_calls', []),
        'token_usage': final.get('token_usage', {'input': 0, 'output': 0}),
    }


# 流式节点（LLM token 经 stream_to_user 直送）与非流式节点（节点结束整体补发切块）
_STREAM_NODES = {'chat', 'search', 'forum'}
_NONSTREAM_NODES = {'problem', 'query', 'unclear', 'exec_step'}


async def run_agent_stream(user_message: str, user_id: int, history: list[dict] = None):
    """流式执行（astream_events v2 翻译为 {meta/content/done} 契约）

    - chat/search/forum：LLM token 经 stream_to_user tag 真流式
    - problem/query/unclear/多步(exec_step)：节点结束整体切块补发（复刻旧版假流式）
    """
    init_state: AgentState = {
        'user_message': user_message, 'user_id': user_id, 'history': history or [],
        'crawled_data': [], 'tool_calls': [], 'step_results': [],
        'total_tokens': {'input': 0, 'output': 0},
    }
    config = {'recursion_limit': 50}
    meta_sent = False
    agent_name, intent = 'chat', 'chat'
    tool_calls: list[dict] = []
    token_usage = {'input': 0, 'output': 0}

    async for ev in _get_graph().astream_events(init_state, version='v2', config=config):
        event = ev['event']
        name = ev.get('name', '')
        data = ev.get('data') or {}

        if event == 'on_chain_end' and name == 'orchestrator':
            out = data.get('output') or {}
            if not meta_sent:
                yield {'type': 'meta', 'understanding': out.get('understanding', ''),
                       'steps': len(out.get('steps', [])) or 1}
                meta_sent = True

        elif event == 'on_chat_model_stream' and 'stream_to_user' in (ev.get('tags') or []):
            chunk = data.get('chunk')
            c = getattr(chunk, 'content', '') if chunk else ''
            if c:
                yield {'type': 'content', 'content': c}

        elif event == 'on_chain_end' and name in (_STREAM_NODES | _NONSTREAM_NODES):
            out = data.get('output') or {}
            if out.get('agent_name'):
                agent_name = out['agent_name']
            if out.get('intent'):
                intent = out['intent']
            if out.get('tool_calls'):
                tool_calls.extend(out['tool_calls'])
            if out.get('token_usage'):
                token_usage = out['token_usage']
            # 非流式节点：reply 未经 token 流送出，节点结束时整体切块补发
            if name in _NONSTREAM_NODES and out.get('reply'):
                reply = out['reply']
                for i in range(0, len(reply), 50):
                    yield {'type': 'content', 'content': reply[i:i + 50]}

    yield {'type': 'done', 'intent': intent, 'agent_name': agent_name,
           'tool_calls': tool_calls, 'token_usage': token_usage}
