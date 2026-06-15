"""
Problem Agent - 出题Agent（算法题生成）
快速模式：预取题目列表 → LLM 一次性生成题目+脚本+解 → 执行验证 → 提交 HOJ
"""
import json
import logging
import re as _re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def _call_llm(messages: list) -> dict:
    """调用LLM API"""
    base_url = settings.LLM_BASE_URL or 'https://api.deepseek.com'
    url = f'{base_url}/v1/chat/completions'
    payload = {
        'model': settings.LLM_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 8192,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url, json=payload,
            headers={'Authorization': f'Bearer {settings.ANTHROPIC_API_KEY}'},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()


async def _call_hoj_api(method: str, path: str, **kwargs) -> dict:
    """调用 HOJ Admin API"""
    async with httpx.AsyncClient() as client:
        login_resp = await client.post(
            f'{settings.HOJ_API_URL}/api/login',
            json={'username': settings.HOJ_ADMIN_USER, 'password': settings.HOJ_ADMIN_PASS},
            timeout=10.0,
        )
        login_resp.raise_for_status()
        token = ''
        for key, value in login_resp.headers.items():
            if key.lower() == 'authorization':
                token = value
                break
        resp = await client.request(
            method, f'{settings.HOJ_API_URL}{path}',
            headers={'Authorization': token, 'Url-Type': 'admin'},
            timeout=30.0, **kwargs,
        )
        resp.raise_for_status()
        return resp.json()


async def execute_problem_task_with_data(user_message: str, user_id: int, crawled_data: list[dict], history: list[dict] = None) -> dict:
    """执行出题任务（快速模式）"""
    import time as _time
    from app.tools.problem_tools import execute_cyaron_script, run_brute_vs_solution, submit_problem_to_hoj

    try:
        start_total = _time.time()

        # Step 1: 预取已有题目列表
        try:
            problems_data = await _call_hoj_api('GET', '/api/admin/problem/get-problem-list?currentPage=1&limit=20')
            existing_titles = []
            if problems_data.get('status') == 200:
                for p in problems_data.get('data', {}).get('records', []):
                    existing_titles.append(p.get('title', ''))
            existing_context = f"已有题目（避免重复）: {', '.join(existing_titles[:10])}" if existing_titles else ""
        except Exception:
            existing_context = ""

        # Step 2: 格式化爬取数据
        context_parts = []
        for i, page in enumerate(crawled_data[:5], 1):
            title = page.get('title', '无标题')
            url = page.get('url', '')
            content = (page.get('markdown') or '')[:3000]
            context_parts.append(f'--- 参考 {i}: {title} ({url}) ---\n{content}')
        crawled_context = '\n\n'.join(context_parts) if context_parts else '（无参考数据，请根据用户描述直接生成题目）'

        # Step 2.5: 提取历史消息中的题目内容（如果有）
        history_context = ''
        if history:
            history_parts = []
            for msg in history[-6:]:  # 最近6条消息
                role = msg.get('role', '')
                content = msg.get('content', '')
                if role == 'assistant' and ('题目' in content or '题解' in content or '输入格式' in content or '输出格式' in content):
                    history_parts.append(f'--- 历史对话中的题目信息 ---\n{content[:2000]}')
            if history_parts:
                history_context = '\n\n'.join(history_parts)

        # Step 3: LLM 一次性生成题目所有内容
        gen_prompt = f"""用户请求: {user_message}

参考资料：
{crawled_context}

{history_context}

{existing_context}

任务：生成一道算法题目，包含完整的题目描述、测试数据生成脚本、暴力解和正解。

题目质量要求：
1. 描述清晰无歧义，输入输出格式明确
2. 示例输入输出必须正确且可验证
3. 测试用例覆盖边界情况（n=1, n=MAX, 特殊值）
4. 暴力解必须正确（可慢），正解必须高效
5. 难度标签与实际难度匹配（0简单/1中等/2困难）

CYaRon 脚本规范（严格遵守，否则脚本无法生成文件）：
- 导入：from cyaron import *
- 随机数：randint(1, 100)  ← 2个参数，不是3个
- 禁止用 print() 输出！必须用 IO 类生成文件！

完整示例（照抄结构，只改逻辑）：
```python
from cyaron import *
for i in range(1, 11):
    io = IO(file_prefix="test", data_id=i)
    n = randint(1, 100)
    arr = [randint(1, 1000) for _ in range(n)]
    io.input_writeln(n)
    io.input_writeln(arr)
    # 计算答案（直接算，不要定义函数）
    ans = sum(arr)
    io.output_writeln(ans)
```

- 创建文件：io = IO(file_prefix='test', data_id=i)  ← 每轮循环都要创建
- 写输入：io.input_writeln(x)  ← 可多次调用
- 写输出：io.output_writeln(正确答案)  ← 直接写答案，不要用 io.output_gen()
- 循环 range(1, 11) 生成10组
- 前几组手动构造边界数据，后面用随机

⚠️ 重要：CYaRon脚本中禁止嵌入暴力解函数！
- CYaRon脚本只负责生成输入数据和写入正确输出
- 对于需要计算答案的题目，直接在脚本中用简单逻辑计算答案
- 不要定义 brute_force/solve 等函数，不要调用复杂算法
- 大数据组（n>1000）的输出必须用数学公式或简单计算，不能用O(n²)算法

返回 JSON 格式（只返回 JSON）：
{{
  "problem_id": "P1050",
  "title": "题目标题",
  "description": "题目描述",
  "input_description": "输入格式",
  "output_description": "输出格式",
  "difficulty": 0,
  "tags": ["标签"],
  "time_limit": 1000,
  "memory_limit": 256,
  "examples": [{{"input": "示例输入", "output": "示例输出"}}],
  "cyaron_script": "完整的CYaRon脚本",
  "brute_force_solution": "完整的C++暴力解",
  "solution": "完整的C++正解"
}}"""

        data = await _call_llm([
            {'role': 'system', 'content': '你是算法竞赛出题专家。根据需求生成完整的题目，包括CYaRon数据生成脚本、暴力解和正解。只返回JSON，不要其他内容。'},
            {'role': 'user', 'content': gen_prompt},
        ])

        content = data['choices'][0]['message']['content'].strip()
        usage = data.get('usage', {})
        token_usage = {'input': usage.get('prompt_tokens', 0), 'output': usage.get('completion_tokens', 0)}

        # 解析 JSON
        json_str = content
        if '```' in json_str:
            json_str = _re.sub(r'```json?\s*', '', json_str)
            json_str = json_str.replace('```', '').strip()

        problem_data = {}
        try:
            if json_str.startswith('{'):
                problem_data = json.loads(json_str)
            else:
                match = _re.search(r'\{.*\}', json_str, _re.DOTALL)
                if match:
                    problem_data = json.loads(match.group())
        except json.JSONDecodeError:
            json_str = _re.sub(r'[\x00-\x1f\x7f]', ' ', json_str)
            json_str = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            try:
                if json_str.startswith('{'):
                    problem_data = json.loads(json_str)
                else:
                    match = _re.search(r'\{.*\}', json_str, _re.DOTALL)
                    if match:
                        problem_data = json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.error(f'JSON 解析失败: {e}')

        # 确保 problem_data 是 dict
        if not isinstance(problem_data, dict):
            problem_data = {}

        # 标准化字段：LLM 可能返回嵌套结构 {"problem": {...}, "cyaron_script": "..."}
        # 或扁平结构 {"title": "...", "cyaron_script": "..."}
        if 'problem' in problem_data and isinstance(problem_data['problem'], dict):
            nested = problem_data['problem']
            # 将嵌套字段提升到顶层（不覆盖已存在的字段）
            for key in ['title', 'description', 'input_description', 'output_description',
                        'difficulty', 'tags', 'time_limit', 'memory_limit', 'examples',
                        'hint', 'problem_id']:
                if key not in problem_data and key in nested:
                    problem_data[key] = nested[key]
            # 处理字段名映射
            if 'input_format' in nested and 'input_description' not in problem_data:
                problem_data['input_description'] = nested['input_format']
            if 'output_format' in nested and 'output_description' not in problem_data:
                problem_data['output_description'] = nested['output_format']
            if 'sample_input' in nested and 'examples' not in problem_data:
                problem_data['examples'] = [{'input': nested['sample_input'], 'output': nested.get('sample_output', '')}]

        # 处理字段名映射
        if 'brute_force' in problem_data and 'brute_force_solution' not in problem_data:
            problem_data['brute_force_solution'] = problem_data['brute_force']
        if 'optimal_solution' in problem_data and 'solution' not in problem_data:
            problem_data['solution'] = problem_data['optimal_solution']

        logger.info(f'生成的 CYaRon 脚本:\n{problem_data.get("cyaron_script", "EMPTY")}')
        logger.info(f'生成的题目标题: {problem_data.get("title", "EMPTY")}')

        if not problem_data.get('title'):
            return {
                'reply': '❌ 题目生成失败：LLM 返回的数据格式不正确',
                'tool_calls': [],
                'token_usage': token_usage,
            }

        # Step 4: 执行 CYaRon 脚本生成测试数据
        script_code = problem_data.get('cyaron_script', '')
        logger.info(f'传给 execute_cyaron_script 的脚本长度: {len(script_code)}')
        logger.info(f'problem_data 的 keys: {list(problem_data.keys())}')

        if not script_code:
            return {
                'reply': '❌ 题目生成失败：LLM 未生成 CYaRon 脚本',
                'tool_calls': [],
                'token_usage': token_usage,
            }

        cyaron_result = await execute_cyaron_script.ainvoke({
            'script_code': script_code,
            'test_count': 10,
        })

        test_cases = cyaron_result.get('test_cases', [])
        if not test_cases:
            return {
                'reply': f'❌ 测试数据生成失败: {cyaron_result.get("error", "未知错误")}',
                'tool_calls': [{'tool_name': 'execute_cyaron_script', 'status': 'failed'}],
                'token_usage': token_usage,
            }

        # Step 5: 对拍验证（取前 3 个小数据验证）
        verify_results = []
        brute_code = problem_data.get('brute_force_solution', '')
        solution_code = problem_data.get('solution', '')

        for tc in test_cases[:3]:
            if len(tc.get('input', '')) > 10000:
                continue
            result = await run_brute_vs_solution.ainvoke({
                'test_input': tc['input'],
                'brute_code': brute_code,
                'solution_code': solution_code,
            })
            verify_results.append(result)

        all_match = all(r.get('match', False) for r in verify_results) if verify_results else False
        failed_cases = [r for r in verify_results if not r.get('match', False)]

        # Step 6: 构造题目数据并提交 HOJ
        # 生成唯一的 problem_id（避免重复）
        try:
            problems_list = await _call_hoj_api('GET', '/api/admin/problem/get-problem-list?currentPage=1&limit=100')
            existing_ids = set()
            if isinstance(problems_list, dict) and problems_list.get('status') == 200:
                data = problems_list.get('data')
                if isinstance(data, dict):
                    for p in data.get('records', []):
                        if isinstance(p, dict):
                            existing_ids.add(p.get('problemId', '').upper())
            # 生成下一个可用的 ID
            max_num = 1000
            for pid in existing_ids:
                if pid.startswith('P') and pid[1:].isdigit():
                    max_num = max(max_num, int(pid[1:]))
            problem_id = f'P{max_num + 1}'
        except Exception as e:
            logger.warning(f'获取题目列表失败: {e}')
            problem_id = problem_data.get('problem_id', 'P9999')

        examples_html = ''
        for ex in problem_data.get('examples', []):
            examples_html += f"<input>{ex.get('input', '')}</input><output>{ex.get('output', '')}</output>"

        samples = [{'input': tc.get('input', ''), 'output': tc.get('output', '')} for tc in test_cases]

        hoj_problem = {
            'problem_id': problem_id,
            'title': problem_data.get('title', ''),
            'description': problem_data.get('description', ''),
            'input': problem_data.get('input_description', ''),
            'output': problem_data.get('output_description', ''),
            'examples': examples_html,
            'hint': problem_data.get('hint', ''),
            'time_limit': problem_data.get('time_limit', 1000),
            'memory_limit': problem_data.get('memory_limit', 256),
            'difficulty': problem_data.get('difficulty', 1),
            'tags': problem_data.get('tags', []),
            'samples': samples,
        }

        submit_result = await submit_problem_to_hoj.ainvoke({
            'problem_data': json.dumps(hoj_problem, ensure_ascii=False),
        })

        duration = int((_time.time() - start_total) * 1000)

        if submit_result.get('success'):
            # 使用生成的 problem_id（HOJ API 不返回 ID）
            display_id = problem_id if problem_id else 'P???'
            verify_status = '✅ 对拍通过' if all_match else '⚠️ 对拍未完全通过（已提交，建议人工检查）'
            reply = f"""✅ 题目创建成功！

| 项目 | 内容 |
|------|------|
| **题目ID** | {display_id} |
| **标题** | {problem_data.get('title', '')} |
| **难度** | {'简单' if problem_data.get('difficulty') == 0 else '中等' if problem_data.get('difficulty') == 1 else '困难'} |
| **测试点** | {len(test_cases)} 组 |
| **对拍验证** | {verify_status} |
| **耗时** | {duration/1000:.1f}秒 |"""
            if failed_cases:
                reply += f"\n\n⚠️ 对拍失败的用例：\n"
                for i, fc in enumerate(failed_cases[:2], 1):
                    reply += f"- 用例{i}: {fc.get('error', '输出不一致')}\n"
        else:
            reply = f"❌ 题目提交失败: {submit_result.get('error', '未知错误')}"

        return {
            'reply': reply,
            'tool_calls': [
                {'tool_name': 'execute_cyaron_script', 'status': 'success', 'test_count': len(test_cases)},
                {'tool_name': 'run_brute_vs_solution', 'status': 'success' if all_match else 'failed'},
                {'tool_name': 'submit_problem_to_hoj', 'status': 'success' if submit_result.get('success') else 'failed'},
            ],
            'token_usage': token_usage,
        }

    except Exception as e:
        logger.error(f'Problem Agent执行失败: {type(e).__name__}: {e}', exc_info=True)
        error_msg = str(e) or type(e).__name__
        return {
            'reply': f'出题Agent执行异常: {error_msg}',
            'tool_calls': [],
            'token_usage': {'input': 0, 'output': 0},
        }
