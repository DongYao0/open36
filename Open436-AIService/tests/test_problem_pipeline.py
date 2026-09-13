import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.agents import problem
from app.tools import problem_tools


class ProblemPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_submit_uses_configured_hoj_username_as_author(self):
        calls = []

        def fake_post(url, **kwargs):
            calls.append((url, kwargs))
            if url.endswith('/api/login'):
                return SimpleNamespace(
                    headers={'Authorization': 'test-token'},
                    raise_for_status=lambda: None,
                )
            return SimpleNamespace(
                headers={}, raise_for_status=lambda: None,
                json=lambda: {'status': 200, 'data': {'id': 99}},
            )

        with patch('requests.post', side_effect=fake_post):
            with patch.object(problem_tools.settings, 'HOJ_ADMIN_USER', 'prod-judge-admin'):
                result = await problem_tools.submit_problem_to_hoj.ainvoke({
                    'problem_data': json.dumps({
                        'problem_id': 'P9999', 'title': '测试题', 'samples': [], 'tags': [],
                    }, ensure_ascii=False),
                })

        self.assertTrue(result['success'])
        self.assertEqual(calls[1][1]['json']['problem']['author'], 'prod-judge-admin')

    async def test_failed_verification_retries_once_then_submits(self):
        original = (problem.gen_node, problem.verify_node, problem.submit_node)
        fake_gen = AsyncMock(side_effect=[
            {'problem_data': {'title': '候选1'}, 'attempts': 1, 'gen_failed': False},
            {'problem_data': {'title': '候选2'}, 'attempts': 2, 'gen_failed': False},
        ])
        fake_verify = AsyncMock(side_effect=[
            {'test_cases': [{}], 'all_match': False,
             'failed_cases': [{'error': '输出不一致'}], 'reply': '第一次失败'},
            {'test_cases': [{}], 'all_match': True, 'failed_cases': [], 'reply': ''},
        ])
        fake_submit = AsyncMock(return_value={'reply': '创建成功'})
        problem.gen_node, problem.verify_node, problem.submit_node = fake_gen, fake_verify, fake_submit
        try:
            result = await problem.build_problem_graph().ainvoke({
                'user_message': '出题', 'user_id': 1, 'history': [], 'crawled_data': [],
                'tool_calls': [], 'gen_failed': False, 'attempts': 0,
            })
        finally:
            problem.gen_node, problem.verify_node, problem.submit_node = original

        self.assertEqual(fake_gen.await_count, 2)
        fake_submit.assert_awaited_once()
        self.assertEqual(result['reply'], '创建成功')

    async def test_two_failed_verifications_never_submit(self):
        original = (problem.gen_node, problem.verify_node, problem.submit_node)
        fake_gen = AsyncMock(side_effect=[
            {'problem_data': {'title': '候选1'}, 'attempts': 1, 'gen_failed': False},
            {'problem_data': {'title': '候选2'}, 'attempts': 2, 'gen_failed': False},
        ])
        fake_verify = AsyncMock(side_effect=[
            {'test_cases': [{}], 'all_match': False,
             'failed_cases': [{'error': '不一致1'}], 'reply': '第一次失败'},
            {'test_cases': [{}], 'all_match': False,
             'failed_cases': [{'error': '不一致2'}], 'reply': '第二次失败'},
        ])
        fake_submit = AsyncMock(return_value={'reply': '不应执行'})
        problem.gen_node, problem.verify_node, problem.submit_node = fake_gen, fake_verify, fake_submit
        try:
            result = await problem.build_problem_graph().ainvoke({
                'user_message': '出题', 'user_id': 1, 'history': [], 'crawled_data': [],
                'tool_calls': [], 'gen_failed': False, 'attempts': 0,
            })
        finally:
            problem.gen_node, problem.verify_node, problem.submit_node = original

        self.assertEqual(fake_gen.await_count, 2)
        fake_submit.assert_not_awaited()
        self.assertEqual(result['reply'], '第二次失败')
