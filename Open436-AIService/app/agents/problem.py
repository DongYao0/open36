"""
Problem Agent - 基于 LangGraph StateGraph 子图的出题流水线

子图：gen(预取+格式化+history+LLM生成+JSON解析) → verify(cyaron造数+对拍) → submit(pid+提交HOJ+reply)
副作用语义逐一保留（对拍失败仍提交+人工检查标注、problem_id=max(P)+1、history 注入）。
"""
import json
import logging
import operator
import re as _re
from typing import Annotated, TypedDict

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from app.config import settings
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)


class ProblemState(TypedDict, total=False):
    user_message: str
    user_id: int
    history: list[dict]
    crawled_data: list[dict]
    problem_data: dict
    test_cases: list[dict]
    all_match: bool
    failed_cases: list[dict]
    reply: str
    tool_calls: Annotated[list[dict], operator.add]
    token_usage: dict
    gen_failed: bool


async def _call_hoj_api(method: str, path: str, **kwargs) -> dict:
    """调用 HOJ Admin API（异步 httpx，GET 查题目列表用）"""
    async with httpx.AsyncClient() as client:
        login_resp = await client.post(
            f'{settings.HOJ_API_URL}/api/login',
            json={'username': settings.HOJ_ADMIN_USER, 'password': settings.HOJ_ADMIN_PASS},
            timeout=10.0,
        )
        login_resp.raise_for_status()
        token = ''
        for k, v in login_resp.headers.items():
            if k.lower() == 'authorization':
                token = v
                break
        resp = await client.request(
            method, f'{settings.HOJ_API_URL}{path}',
            headers={'Authorization': token, 'Url-Type': 'admin'}, timeout=30.0, **kwargs,
        )
        resp.raise_for_status()
        return resp.json()


def _parse_problem_json(content: str) -> dict:
    """解析 LLM 返回的题目 JSON（去 markdown/控制字符/正则兜底/嵌套标准化）"""
    json_str = content
    if '```' in json_str:
        json_str = _re.sub(r'```json?\s*', '', json_str).replace('```', '').strip()
    problem_data = {}
    try:
        problem_data = json.loads(json_str) if json_str.startswith('{') else \
            json.loads(_re.search(r'\{.*\}', json_str, _re.DOTALL).group()) if _re.search(r'\{.*\}', json_str, _re.DOTALL) else {}
    except json.JSONDecodeError:
        cleaned = _re.sub(r'[\x00-\x1f\x7f]', ' ', json_str).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        try:
            m = _re.search(r'\{.*\}', cleaned, _re.DOTALL)
            problem_data = json.loads(m.group()) if m else {}
        except json.JSONDecodeError as e:
            logger.error(f'JSON 解析失败: {e}')

    if not isinstance(problem_data, dict):
        problem_data = {}

    # 嵌套结构 {problem:{...}} 提升
    if 'problem' in problem_data and isinstance(problem_data['problem'], dict):
        nested = problem_data['problem']
        for key in ['title', 'description', 'input_description', 'output_description',
                    'difficulty', 'tags', 'time_limit', 'memory_limit', 'examples', 'hint', 'problem_id']:
            if key not in problem_data and key in nested:
                problem_data[key] = nested[key]
        if 'input_format' in nested and 'input_description' not in problem_data:
            problem_data['input_description'] = nested['input_format']
        if 'output_format' in nested and 'output_description' not in problem_data:
            problem_data['output_description'] = nested['output_format']
    # 字段名映射
    if 'brute_force' in problem_data and 'brute_force_solution' not in problem_data:
        problem_data['brute_force_solution'] = problem_data['brute_force']
    if 'optimal_solution' in problem_data and 'solution' not in problem_data:
        problem_data['solution'] = problem_data['optimal_solution']
    return problem_data


async def gen_node(state: ProblemState) -> dict:
    """gen 节点：预取题目列表 + 格式化参考 + history 注入 + LLM 生成 + JSON 解析"""
    user_message = state['user_message']

    # Step1 预取已有题目（避免重复）
    existing_context = ''
    try:
        pd = await _call_hoj_api('GET', '/api/admin/problem/get-problem-list?currentPage=1&limit=20')
        if pd.get('status') == 200:
            titles = [p.get('title', '') for p in pd.get('data', {}).get('records', [])]
            existing_context = f"已有题目（避免重复）: {', '.join(titles[:10])}" if any(titles) else ''
    except Exception:
        pass

    # Step2 格式化爬取参考
    parts = [f'--- 参考 {i}: {pg.get("title", "无标题")} ({pg.get("url", "")}) ---\n{(pg.get("markdown") or "")[:3000]}'
             for i, pg in enumerate((state.get('crawled_data') or [])[:5], 1)]
    crawled_context = '\n\n'.join(parts) or '（无参考数据，请根据用户描述直接生成题目）'

    # Step2.5 history 注入（仅 problem，最近6条 assistant 含题目词）
    history_context = ''
    for msg in (state.get('history') or [])[-6:]:
        if msg.get('role') == 'assistant' and any(k in msg.get('content', '') for k in ('题目', '题解', '输入格式', '输出格式')):
            history_context += f'\n\n--- 历史对话中的题目信息 ---\n{msg["content"][:2000]}'

    gen_prompt = f"""用户请求: {user_message}

参考资料：
{crawled_context}
{history_context}
{existing_context}

任务：生成一道算法题目（描述+测试数据生成脚本+暴力解+正解）。

CYaRon 脚本规范（严格遵守，否则无法生成文件）：
- from cyaron import *
- randint(1, 100) 用2参数
- 禁止 print()，必须用 IO 类：io = IO(file_prefix='test', data_id=i)
- io.input_writeln(x) 写输入，io.output_writeln(答案) 写输出
- 循环 range(1,11) 生成10组，前几组边界数据
- 禁止嵌入暴力解函数，直接简单计算答案；大数据组用数学公式不用O(n²)

示例：
```python
from cyaron import *
for i in range(1, 11):
    io = IO(file_prefix="test", data_id=i)
    n = randint(1, 100)
    arr = [randint(1, 1000) for _ in range(n)]
    io.input_writeln(n)
    io.input_writeln(arr)
    io.output_writeln(sum(arr))
```

返回JSON（只返回JSON）：
{{"problem_id":"P1050","title":"...","description":"...","input_description":"...","output_description":"...","difficulty":0,"tags":["..."],"time_limit":1000,"memory_limit":256,"examples":[{{"input":"...","output":"..."}}],"cyaron_script":"...","brute_force_solution":"...","solution":"..."}}"""

    msg = await get_chat_model(temperature=0.7, max_tokens=8192, timeout=120).ainvoke([
        SystemMessage(content='你是算法竞赛出题专家。根据需求生成完整题目（含CYaRon脚本、暴力解、正解）。只返回JSON。'),
        HumanMessage(content=gen_prompt),
    ])
    usage = getattr(msg, 'usage_metadata', None) or {}
    token_usage = {'input': usage.get('input_tokens', 0), 'output': usage.get('output_tokens', 0)}

    problem_data = _parse_problem_json((msg.content or '').strip())
    logger.info(f'题目标题: {problem_data.get("title", "EMPTY")} | 脚本长度: {len(problem_data.get("cyaron_script", ""))}')

    if not problem_data.get('title'):
        return {'problem_data': problem_data, 'token_usage': token_usage, 'gen_failed': True,
                'reply': '❌ 题目生成失败：LLM 返回的数据格式不正确'}
    if not problem_data.get('cyaron_script'):
        return {'problem_data': problem_data, 'token_usage': token_usage, 'gen_failed': True,
                'reply': '❌ 题目生成失败：LLM 未生成 CYaRon 脚本'}
    return {'problem_data': problem_data, 'token_usage': token_usage, 'gen_failed': False}


async def verify_node(state: ProblemState) -> dict:
    """verify 节点：cyaron 造数 + 对拍前3小数据（对拍失败不阻断提交）"""
    from app.tools.problem_tools import execute_cyaron_script, run_brute_vs_solution
    problem_data = state['problem_data']

    cyaron_result = await execute_cyaron_script.ainvoke(
        {'script_code': problem_data.get('cyaron_script', ''), 'test_count': 10})
    test_cases = cyaron_result.get('test_cases', [])
    if not test_cases:
        return {'test_cases': [], 'gen_failed': True,
                'reply': f'❌ 测试数据生成失败: {cyaron_result.get("error", "未知错误")}',
                'tool_calls': [{'tool_name': 'execute_cyaron_script', 'status': 'failed'}]}

    brute = problem_data.get('brute_force_solution', '')
    sol = problem_data.get('solution', '')
    verify_results = []
    for tc in test_cases[:3]:
        if len(tc.get('input', '')) > 10000:
            continue
        r = await run_brute_vs_solution.ainvoke(
            {'test_input': tc['input'], 'brute_code': brute, 'solution_code': sol})
        verify_results.append(r)
    all_match = all(r.get('match', False) for r in verify_results) if verify_results else False
    failed_cases = [r for r in verify_results if not r.get('match', False)]

    return {'test_cases': test_cases, 'all_match': all_match, 'failed_cases': failed_cases,
            'tool_calls': [{'tool_name': 'execute_cyaron_script', 'status': 'success', 'test_count': len(test_cases)},
                           {'tool_name': 'run_brute_vs_solution', 'status': 'success' if all_match else 'failed'}]}


async def submit_node(state: ProblemState) -> dict:
    """submit 节点：计算 problem_id=max(P)+1 + 提交 HOJ + 构造 reply（对拍失败仍提交）"""
    from app.tools.problem_tools import submit_problem_to_hoj
    problem_data = state['problem_data']
    test_cases = state.get('test_cases', [])
    all_match = state.get('all_match', False)
    failed_cases = state.get('failed_cases', [])

    # problem_id = max(P\d+) + 1
    problem_id = problem_data.get('problem_id', 'P9999')
    try:
        pl = await _call_hoj_api('GET', '/api/admin/problem/get-problem-list?currentPage=1&limit=100')
        existing_ids = set()
        if isinstance(pl, dict) and pl.get('status') == 200:
            data = pl.get('data')
            if isinstance(data, dict):
                for p in data.get('records', []):
                    if isinstance(p, dict):
                        existing_ids.add(str(p.get('problemId', '')).upper())
        max_num = 1000
        for pid in existing_ids:
            if pid.startswith('P') and pid[1:].isdigit():
                max_num = max(max_num, int(pid[1:]))
        problem_id = f'P{max_num + 1}'
    except Exception as e:
        logger.warning(f'获取题目列表失败: {e}')

    examples_html = ''
    for ex in problem_data.get('examples', []):
        examples_html += f"<input>{ex.get('input', '')}</input><output>{ex.get('output', '')}</output>"
    samples = [{'input': tc.get('input', ''), 'output': tc.get('output', '')} for tc in test_cases]
    hoj_problem = {
        'problem_id': problem_id, 'title': problem_data.get('title', ''),
        'description': problem_data.get('description', ''), 'input': problem_data.get('input_description', ''),
        'output': problem_data.get('output_description', ''), 'examples': examples_html,
        'hint': problem_data.get('hint', ''), 'time_limit': problem_data.get('time_limit', 1000),
        'memory_limit': problem_data.get('memory_limit', 256), 'difficulty': problem_data.get('difficulty', 1),
        'tags': problem_data.get('tags', []), 'samples': samples,
    }

    submit_result = await submit_problem_to_hoj.ainvoke({'problem_data': json.dumps(hoj_problem, ensure_ascii=False)})

    if submit_result.get('success'):
        verify_status = '✅ 对拍通过' if all_match else '⚠️ 对拍未完全通过（已提交，建议人工检查）'
        diff = '简单' if problem_data.get('difficulty') == 0 else '中等' if problem_data.get('difficulty') == 1 else '困难'
        reply = (f"✅ 题目创建成功！\n\n| 项目 | 内容 |\n|------|------|\n"
                 f"| **题目ID** | {problem_id} |\n| **标题** | {problem_data.get('title', '')} |\n"
                 f"| **难度** | {diff} |\n| **测试点** | {len(test_cases)} 组 |\n| **对拍验证** | {verify_status} |")
        if failed_cases:
            reply += "\n\n⚠️ 对拍失败的用例：\n"
            for i, fc in enumerate(failed_cases[:2], 1):
                reply += f"- 用例{i}: {fc.get('error', '输出不一致')}\n"
    else:
        reply = f"❌ 题目提交失败: {submit_result.get('error', '未知错误')}"

    return {'reply': reply, 'problem_id': problem_id,
            'tool_calls': [{'tool_name': 'submit_problem_to_hoj',
                            'status': 'success' if submit_result.get('success') else 'failed'}]}


def build_problem_graph():
    """构建 problem 子图：gen →(条件)→ verify →(条件)→ submit"""
    g = StateGraph(ProblemState)
    g.add_node('gen', gen_node)
    g.add_node('verify', verify_node)
    g.add_node('submit', submit_node)
    g.add_edge(START, 'gen')
    g.add_conditional_edges('gen', lambda s: END if s.get('gen_failed') else 'verify',
                            {END: END, 'verify': 'verify'})
    g.add_conditional_edges('verify',
                            lambda s: END if (s.get('gen_failed') or not s.get('test_cases')) else 'submit',
                            {END: END, 'submit': 'submit'})
    g.add_edge('submit', END)
    return g.compile()


_PROBLEM_GRAPH = None


def get_problem_agent():
    global _PROBLEM_GRAPH
    if _PROBLEM_GRAPH is None:
        _PROBLEM_GRAPH = build_problem_graph()
    return _PROBLEM_GRAPH


async def run_problem(user_message: str, user_id: int, crawled_data: list[dict] = None,
                      history: list[dict] = None) -> dict:
    """执行 problem 子图，返回 {reply, tool_calls, token_usage}"""
    init = {'user_message': user_message, 'user_id': user_id, 'history': history or [],
            'crawled_data': crawled_data or [], 'tool_calls': [], 'gen_failed': False}
    try:
        final = await get_problem_agent().ainvoke(init, config={'recursion_limit': 20})
    except Exception as e:
        logger.error(f'Problem 子图异常: {type(e).__name__}: {e}', exc_info=True)
        return {'reply': f'出题Agent执行异常: {str(e) or type(e).__name__}',
                'tool_calls': [], 'token_usage': {'input': 0, 'output': 0}}
    return {'reply': final.get('reply', ''), 'tool_calls': final.get('tool_calls', []),
            'token_usage': final.get('token_usage', {'input': 0, 'output': 0})}
