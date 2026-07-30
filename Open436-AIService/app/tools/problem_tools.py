"""
出题工具 - CYaRon 执行器 + Validator + 对拍器 + HOJ 提交
"""
import asyncio
import json
import logging
import os
import tempfile
import shutil
from pathlib import Path

from langchain_core.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)


@tool
async def execute_cyaron_script(script_code: str, test_count: int = 10) -> dict:
    """
    执行 CYaRon 脚本生成测试数据。

    Args:
        script_code: CYaRon Python 脚本代码
        test_count: 生成测试点数量，默认10
    Returns:
        {"success": bool, "test_cases": [{"input": "...", "output": "..."}], "error": "..."}
    """
    try:
        # 创建临时目录
        work_dir = tempfile.mkdtemp(prefix='cyaron_')

        # 修复脚本：将 output_gen() 替换为 output_writeln()
        # 因为 output_gen 需要编译好的可执行文件，在 Windows 上不可用
        import re as _re
        fixed_script = script_code
        # 匹配 io.output_gen(...) 和 output_gen(...) 各种写法
        fixed_script = _re.sub(r'output_gen\s*\([^)]*\)', 'output_writeln(0)', fixed_script)

        # 修复 random() -> random.random()：LLM 常把 import random 后的模块当函数调用
        # 只替换孤立的 random()，不替换 xxx.random() 或 from random import random 后的调用
        fixed_script = _re.sub(r'(?<![\w.])random\s*\(\s*\)', 'random.random()', fixed_script)
        # 如果修复后用到了 random.random() 但没有 import random，补上
        if 'random.random()' in fixed_script and 'import random' not in fixed_script:
            fixed_script = 'import random\n' + fixed_script

        # 检测脚本是否使用了 IO 类（CYaRon 必须用 IO 生成文件，print() 不会生成文件）
        if 'IO(' not in fixed_script and 'io.input' not in fixed_script.lower():
            return {
                'success': False,
                'error': 'CYaRon 脚本缺少 IO 类，无法生成测试数据文件。必须使用 io = IO(file_prefix="test", data_id=i) 创建文件，用 io.input_writeln() 和 io.output_writeln() 写入数据。禁止使用 print()。',
                'test_cases': [],
            }

        # 写入 CYaRon 脚本
        script_path = os.path.join(work_dir, 'gen.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(fixed_script)

        # 调试：记录脚本内容
        logger.info(f'CYaRon 原始脚本:\n{script_code}')
        logger.info(f'CYaRon 修复后脚本:\n{fixed_script}')

        # 获取 venv Python 路径
        import sys
        venv_python = sys.executable

        # 执行脚本（使用 venv Python，确保能导入 cyaron）
        proc = await asyncio.create_subprocess_exec(
            venv_python, script_path,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode != 0:
            return {
                'success': False,
                'error': f'CYaRon 脚本执行失败: {stderr.decode("utf-8", errors="replace")}',
                'test_cases': [],
            }

        # 列出生成的文件
        generated_files = os.listdir(work_dir)
        logger.info(f'CYaRon 生成的文件: {generated_files}')

        # 读取生成的测试数据（支持多种文件命名格式）
        test_cases = []
        # 尝试多种命名格式: 1.in, test1.in, test_1.in
        for i in range(1, test_count + 1):
            in_path = None
            out_path = None
            # 格式1: 1.in / 1.out
            if os.path.exists(os.path.join(work_dir, f'{i}.in')):
                in_path = os.path.join(work_dir, f'{i}.in')
                out_path = os.path.join(work_dir, f'{i}.out')
            # 格式2: test1.in / test1.out
            elif os.path.exists(os.path.join(work_dir, f'test{i}.in')):
                in_path = os.path.join(work_dir, f'test{i}.in')
                out_path = os.path.join(work_dir, f'test{i}.out')
            # 格式3: test_1.in / test_1.out
            elif os.path.exists(os.path.join(work_dir, f'test_{i}.in')):
                in_path = os.path.join(work_dir, f'test_{i}.in')
                out_path = os.path.join(work_dir, f'test_{i}.out')

            if in_path and os.path.exists(in_path):
                with open(in_path, 'r', encoding='utf-8') as f:
                    input_data = f.read()
                output_data = ''
                if out_path and os.path.exists(out_path):
                    with open(out_path, 'r', encoding='utf-8') as f:
                        output_data = f.read()
                test_cases.append({
                    'id': i,
                    'input': input_data,
                    'output': output_data,
                })

        # 清理
        shutil.rmtree(work_dir, ignore_errors=True)

        if not test_cases:
            return {
                'success': False,
                'error': f'CYaRon 脚本执行成功但未生成测试数据文件。生成的文件: {generated_files}',
                'test_cases': [],
            }

        return {
            'success': True,
            'test_cases': test_cases,
            'total': len(test_cases),
        }

    except asyncio.TimeoutError:
        return {'success': False, 'error': 'CYaRon 脚本执行超时(60秒)', 'test_cases': []}
    except Exception as e:
        logger.error(f'CYaRon 执行失败: {e}')
        return {'success': False, 'error': str(e), 'test_cases': []}


@tool
async def run_brute_vs_solution(
    test_input: str,
    brute_code: str,
    solution_code: str,
    language: str = 'cpp',
) -> dict:
    """
    对拍：运行暴力解和正解，比较输出是否一致。

    Args:
        test_input: 测试输入数据
        brute_code: 暴力解代码
        solution_code: 正解代码
        language: 代码语言，默认 cpp
    Returns:
        {"match": bool, "brute_output": "...", "solution_output": "...", "error": "..."}
    """
    work_dir = tempfile.mkdtemp(prefix='verify_')

    try:
        # 写入代码文件
        brute_path = os.path.join(work_dir, 'brute.cpp')
        solution_path = os.path.join(work_dir, 'solution.cpp')
        input_path = os.path.join(work_dir, 'input.in')

        with open(brute_path, 'w', encoding='utf-8') as f:
            f.write(brute_code)
        with open(solution_path, 'w', encoding='utf-8') as f:
            f.write(solution_code)
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(test_input)

        # 编译暴力解
        brute_exe = os.path.join(work_dir, 'brute.exe')
        proc = await asyncio.create_subprocess_exec(
            'g++', '-O2', '-o', brute_exe, brute_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if proc.returncode != 0:
            return {'match': False, 'error': f'暴力解编译失败: {stderr.decode()}', 'brute_output': '', 'solution_output': ''}

        # 编译正解
        solution_exe = os.path.join(work_dir, 'solution.exe')
        proc = await asyncio.create_subprocess_exec(
            'g++', '-O2', '-o', solution_exe, solution_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if proc.returncode != 0:
            return {'match': False, 'error': f'正解编译失败: {stderr.decode()}', 'brute_output': '', 'solution_output': ''}

        # 运行暴力解
        with open(input_path, 'r') as f:
            proc = await asyncio.create_subprocess_exec(
                brute_exe,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(input=test_input.encode()), timeout=10
            )
            brute_output = stdout.decode().strip()

        # 运行正解
        with open(input_path, 'r') as f:
            proc = await asyncio.create_subprocess_exec(
                solution_exe,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(input=test_input.encode()), timeout=10
            )
            solution_output = stdout.decode().strip()

        # 比较输出
        match = brute_output == solution_output

        return {
            'match': match,
            'brute_output': brute_output[:1000],
            'solution_output': solution_output[:1000],
            'error': '' if match else '输出不一致',
        }

    except asyncio.TimeoutError:
        return {'match': False, 'error': '执行超时', 'brute_output': '', 'solution_output': ''}
    except Exception as e:
        return {'match': False, 'error': str(e), 'brute_output': '', 'solution_output': ''}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


@tool
async def submit_problem_to_hoj(problem_data: str) -> dict:
    """
    将题目提交到 HOJ 平台。

    Args:
        problem_data: JSON 格式的题目数据，包含:
            - title: 题目标题
            - description: 题目描述(HTML)
            - input: 输入说明
            - output: 输出说明
            - examples: 示例(HTML)
            - time_limit: 时间限制(ms)
            - memory_limit: 内存限制(MB)
            - difficulty: 难度(0/1/2)
            - samples: 测试用例列表 [{"input": "...", "output": "..."}]
            - tags: 标签列表
    Returns:
        {"success": bool, "problem_id": "...", "error": "..."}
    """
    try:
        import httpx

        data = json.loads(problem_data) if isinstance(problem_data, str) else problem_data

        # 获取 HOJ token（使用 requests 库，httpx 会丢失 Authorization 响应头）
        import requests as req_lib
        login_resp = req_lib.post(
            f'{settings.HOJ_API_URL}/api/login',
            json={'username': settings.HOJ_ADMIN_USER, 'password': settings.HOJ_ADMIN_PASS},
            timeout=10.0,
        )
        login_resp.raise_for_status()
        token = login_resp.headers.get('Authorization', '')
        logger.info(f'HOJ token found: {bool(token)}, length: {len(token)}')

        # 构造题目数据
        # 构造题目数据
        samples = data.get('samples', [])
        examples_html = ''
        for s in samples[:3]:
            examples_html += f"<input>{s.get('input', '')}</input><output>{s.get('output', '')}</output>"

        problem_payload = {
            'problem': {
                'problemId': data.get('problem_id', ''),
                'title': data.get('title', ''),
                'author': 'root',  # HOJ 管理员用户名
                'description': data.get('description', ''),
                'input': data.get('input', ''),
                'output': data.get('output', ''),
                'examples': examples_html,
                'hint': data.get('hint', ''),
                'timeLimit': data.get('time_limit', 1000),
                'memoryLimit': data.get('memory_limit', 256),
                'stackLimit': 128,
                'difficulty': data.get('difficulty', 1),
                'type': 0,
                'auth': 1,
                'judgeMode': 'default',
                'judgeCaseMode': 'default',
                'codeShare': True,
                'ioScore': 100,
            },
            'samples': samples,
            'tags': [{'name': t} for t in data.get('tags', [])],
            'languages': [{'id': 1}, {'id': 3}, {'id': 9}, {'id': 10}],  # C, C++, Java, Python3
            'isUploadTestCase': False,
            'judgeMode': 'default',
        }

        # 提交到 HOJ（使用 requests 库）
        resp = req_lib.post(
            f'{settings.HOJ_API_URL}/api/admin/problem',
            headers={'Authorization': token, 'Url-Type': 'admin'},
            json=problem_payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get('status') == 200:
            # data 可能是 null 或 dict
            data = result.get('data')
            problem_id = None
            if isinstance(data, dict):
                problem_id = data.get('id')
            return {
                'success': True,
                'problem_id': problem_id,
                'error': '',
            }
        else:
            return {
                'success': False,
                'problem_id': None,
                'error': result.get('msg', '未知错误'),
            }

    except Exception as e:
        logger.error(f'HOJ 提交失败: {e}')
        return {'success': False, 'problem_id': None, 'error': str(e)}
