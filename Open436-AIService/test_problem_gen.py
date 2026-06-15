"""
测试A+B问题生成 - 不提交到HOJ
"""
import asyncio
import json
import sys
import os

# Windows编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.problem_tools import execute_cyaron_script, run_brute_vs_solution


async def test_ab_problem():
    """测试生成A+B问题"""

    # 模拟LLM生成的A+B题目数据
    problem_data = {
        "problem_id": "P1001",
        "title": "A+B Problem",
        "description": "给定两个整数 A 和 B，计算它们的和 A + B。",
        "input_description": "输入一行，包含两个整数 A 和 B，用空格分隔。(1 ≤ A, B ≤ 1000)",
        "output_description": "输出一行，包含一个整数，表示 A + B 的值。",
        "difficulty": 0,
        "tags": ["入门", "模拟"],
        "time_limit": 1000,
        "memory_limit": 256,
        "examples": [
            {"input": "3 5", "output": "8"},
            {"input": "100 200", "output": "300"}
        ],
        "cyaron_script": """from cyaron import *
import random

for i in range(1, 9):
    io = IO(file_prefix="test", data_id=i)
    if i <= 3:
        # 小数据
        a = randint(1, 10)
        b = randint(1, 10)
    elif i <= 6:
        # 中等数据
        a = randint(10, 100)
        b = randint(10, 100)
    else:
        # 边界数据
        a = randint(900, 1000)
        b = randint(900, 1000)
    io.input_writeln(a, b)
    io.output_writeln(a + b)
""",
        "brute_force_solution": """#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
""",
        "solution": """#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
"""
    }

    print("=" * 60)
    print("🧪 测试A+B问题生成")
    print("=" * 60)

    # Step 1: 执行CYaRon脚本生成测试数据
    print("\n📦 Step 1: 执行CYaRon脚本生成测试数据...")
    script_code = problem_data.get('cyaron_script', '')
    print(f"脚本长度: {len(script_code)} 字符")

    cyaron_result = await execute_cyaron_script.ainvoke({
        'script_code': script_code,
        'test_count': 10,
    })

    print(f"CYaRon结果: {json.dumps(cyaron_result, ensure_ascii=False, indent=2)}")

    if not cyaron_result.get('test_cases'):
        print(f"❌ 测试数据生成失败: {cyaron_result.get('error', '未知错误')}")
        return

    test_cases = cyaron_result['test_cases']
    print(f"✅ 生成了 {len(test_cases)} 组测试数据")

    # 显示前3组测试数据
    for i, tc in enumerate(test_cases[:3], 1):
        print(f"\n--- 测试点 {i} ---")
        print(f"输入: {tc['input'].strip()}")
        print(f"输出: {tc['output'].strip()}")

    # Step 2: 对拍验证
    print("\n🔍 Step 2: 对拍验证 (暴力解 vs 正解)...")
    brute_code = problem_data.get('brute_force_solution', '')
    solution_code = problem_data.get('solution', '')

    verify_results = []
    for tc in test_cases[:3]:
        if len(tc.get('input', '')) > 10000:
            continue
        result = await run_brute_vs_solution.ainvoke({
            'test_input': tc['input'],
            'brute_code': brute_code,
            'solution_code': solution_code,
        })
        verify_results.append(result)
        status = "✅ 匹配" if result.get('match') else "❌ 不匹配"
        print(f"测试点: {status}")
        if not result.get('match'):
            print(f"  错误: {result.get('error', '无')}")
            print(f"  暴力解输出: {result.get('brute_output', '无')[:200]}")
            print(f"  正解输出: {result.get('solution_output', '无')[:200]}")

    all_match = all(r.get('match', False) for r in verify_results) if verify_results else False

    # Step 3: 构造HOJ提交数据（仅预览，不提交）
    print("\n📋 Step 3: 预览HOJ提交数据...")

    examples_html = ''
    for ex in problem_data.get('examples', []):
        examples_html += f"<input>{ex.get('input', '')}</input><output>{ex.get('output', '')}</output>"

    samples = [{'input': tc.get('input', ''), 'output': tc.get('output', '')} for tc in test_cases]

    hoj_problem = {
        'problem_id': problem_data.get('problem_id', 'P1001'),
        'title': problem_data.get('title', ''),
        'description': problem_data.get('description', ''),
        'input': problem_data.get('input_description', ''),
        'output': problem_data.get('output_description', ''),
        'examples': examples_html,
        'hint': problem_data.get('hint', ''),
        'time_limit': problem_data.get('time_limit', 1000),
        'memory_limit': problem_data.get('memory_limit', 256),
        'difficulty': problem_data.get('difficulty', 0),
        'tags': problem_data.get('tags', []),
        'samples': samples,
    }

    print(f"\n题目ID: {hoj_problem['problem_id']}")
    print(f"标题: {hoj_problem['title']}")
    print(f"难度: {'简单' if hoj_problem['difficulty'] == 0 else '中等' if hoj_problem['difficulty'] == 1 else '困难'}")
    print(f"标签: {', '.join(hoj_problem['tags'])}")
    print(f"测试点数: {len(samples)}")
    print(f"对拍验证: {'✅ 全部通过' if all_match else '⚠️ 未完全通过'}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！题目数据已生成，未提交到HOJ。")
    print("=" * 60)

    # 返回完整数据供查看
    return {
        'problem_data': problem_data,
        'hoj_payload': hoj_problem,
        'test_cases_count': len(test_cases),
        'verify_passed': all_match,
    }


if __name__ == '__main__':
    result = asyncio.run(test_ab_problem())
