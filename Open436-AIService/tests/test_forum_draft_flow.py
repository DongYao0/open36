import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.agents import forum_draft
from app.agents.graph import orchestrator_node
from app.services.chat_service import _active_streams, stop_chat
from app.tools import forum_tools


def payload(post_type='tech', title='上下文工程实战指南', suffix='初稿'):
    return json.dumps({
        'post_type': post_type,
        'title': title,
        'summary': f'这是一段用于验证{suffix}的完整摘要，说明读者可以获得的内容。',
        'content': f'这是{suffix}的完整正文，包含必要的技术说明和可执行建议。',
        'resource_url': 'https://github.com/open436/example' if post_type == 'resource' else '',
    }, ensure_ascii=False)


class FakeModel:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.prompts = []

    async def ainvoke(self, messages):
        self.prompts.append(messages[-1].content)
        return SimpleNamespace(content=next(self.replies))


class ForumDraftFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_model = forum_draft.get_chat_model
        self.original_sections = forum_draft.list_sections
        self.original_create = forum_draft.create_post
        self.original_search = forum_draft.search_web
        self.created = AsyncMock(return_value={'id': 42})
        forum_draft.list_sections = SimpleNamespace(ainvoke=AsyncMock(return_value={
            'results': [{'id': 3, 'name': '技术交流'}, {'id': 5, 'name': '资源分享'}]
        }))
        forum_draft.create_post = SimpleNamespace(ainvoke=self.created)
        forum_draft.search_web = SimpleNamespace(ainvoke=AsyncMock(return_value=[]))

    def tearDown(self):
        forum_draft.get_chat_model = self.original_model
        forum_draft.list_sections = self.original_sections
        forum_draft.create_post = self.original_create
        forum_draft.search_web = self.original_search

    async def test_tech_post_only_publishes_after_explicit_command(self):
        model = FakeModel([payload(), payload(title='上下文工程实战指南（优化）')])
        forum_draft.get_chat_model = lambda **_: model
        draft = await forum_draft.run_forum_draft('生成一篇技术交流帖子，主题是上下文工程', 9, [])
        self.created.assert_not_awaited()
        published = await forum_draft.run_forum_draft('上传帖子', 9, [
            {'role': 'assistant', 'content': draft['reply']}
        ])
        self.created.assert_awaited_once()
        self.assertIn('技术交流已发布', published['reply'])
        self.assertEqual(self.created.await_args.args[0]['section_id'], 3)

    async def test_resource_draft_can_be_edited_twice_before_publish(self):
        model = FakeModel([
            payload('resource', 'AI 工具资源清单', '初稿'),
            payload('resource', 'AI 工具资源清单（5 项）', '减少到5条'),
            payload('resource', 'AI 工具资源清单（5 项）', '扩展提示词说明'),
            payload('resource', 'AI 工具资源清单（5 项）', '最终稿'),
        ])
        forum_draft.get_chat_model = lambda **_: model
        first = await forum_draft.run_forum_draft('生成资源分享帖子，推荐 AI 工具', 9, [])
        second = await forum_draft.run_forum_draft('把10条减少到5条吧', 9, [
            {'role': 'assistant', 'content': first['reply']}
        ])
        third = await forum_draft.run_forum_draft('再扩展一段，添加提示词相关内容', 9, [
            {'role': 'assistant', 'content': second['reply']}
        ])
        self.created.assert_not_awaited()
        await forum_draft.run_forum_draft('现在上传资源帖子', 9, [
            {'role': 'assistant', 'content': third['reply']}
        ])
        sent = self.created.await_args.args[0]
        self.assertEqual(sent['section_id'], 5)
        self.assertEqual(sent['resource_url'], 'https://github.com/open436/example')
        self.assertIn('再扩展一段', model.prompts[2])

    def test_fuzzy_followup_routes_to_existing_draft(self):
        history = [{'role': 'assistant', 'content': forum_draft._display_draft(
            forum_draft._parse_draft(payload(), None))}]
        self.assertTrue(forum_draft.is_draft_followup('那改发布信息吧', history))
        self.assertTrue(forum_draft.is_draft_followup('再扩展一段', history))
        self.assertFalse(forum_draft._should_publish('那改发布信息吧'))

    async def test_graph_routes_fuzzy_followup_to_forum(self):
        history = [{'role': 'assistant', 'content': forum_draft._display_draft(
            forum_draft._parse_draft(payload(), None))}]
        plan = await orchestrator_node({'user_message': '把10条减少到5条吧', 'history': history})
        self.assertEqual(plan['steps'][0]['agent'], 'forum')

    async def test_stop_chat_cancels_active_task(self):
        blocker = asyncio.create_task(asyncio.sleep(10))
        _active_streams['test-stop'] = blocker
        self.assertTrue(stop_chat('test-stop'))
        with self.assertRaises(asyncio.CancelledError):
            await blocker
        _active_streams.pop('test-stop', None)

    async def test_resource_post_writes_link_into_final_content(self):
        captured = {}
        original = forum_tools.call_internal

        async def fake_call(*_, **kwargs):
            captured.update(kwargs['json'])
            return {'id': 42}

        forum_tools.call_internal = fake_call
        try:
            await forum_tools.create_post.ainvoke({
                'title': '资源测试标题', 'summary': '这是一段不少于二十字的资源卡片摘要，用于验证字段映射。',
                'content': '资源的使用步骤与适用人群说明。', 'section_id': 5, 'author_id': 9,
                'resource_url': 'https://github.com/open436/example',
            })
        finally:
            forum_tools.call_internal = original
        self.assertIn('[访问资源](https://github.com/open436/example)', captured['content'])

    async def test_explicit_search_is_recorded_and_sources_survive_publish(self):
        model = FakeModel([payload(title='Python 最新特性说明')])
        forum_draft.get_chat_model = lambda **_: model
        forum_draft.search_web = SimpleNamespace(ainvoke=AsyncMock(return_value=[{
            'title': 'Python 官方文档', 'url': 'https://docs.python.org/3/whatsnew/',
            'content': 'Python 最新版本说明',
        }]))

        message = ('请联网搜索 Python 3.14 的正式特性，生成一篇技术交流帖子草稿。'
                   '标题必须包含【完全修复验收-20260912】，先不要发布。')
        draft = await forum_draft.run_forum_draft(message, 9, [])
        forum_draft.search_web.ainvoke.assert_awaited_once_with({
            'query': 'Python 3.14 的正式特性', 'max_results': 5,
        })
        self.assertEqual(draft['tool_calls'][0]['tool_name'], 'search_web')
        self.assertEqual(draft['tool_calls'][0]['status'], 'success')
        self.assertEqual(draft['tool_calls'][0]['tool_args']['query'], 'Python 3.14 的正式特性')
        self.assertIn('## 参考来源', draft['reply'])

        await forum_draft.run_forum_draft('现在发布帖子', 9, [
            {'role': 'assistant', 'content': draft['reply']}
        ])
        sent = self.created.await_args.args[0]
        self.assertNotIn('sources', sent)
        self.assertIn('https://docs.python.org/3/whatsnew/', sent['content'])
        self.assertEqual(len(model.prompts), 1)

    def test_search_query_keeps_subject_and_removes_workflow_commands(self):
        message = ('请先联网搜索基础数组求和题型作为参考，再生成并提交一道简单算法题到 HOJ。'
                   '题目标题必须包含【完全修复验收-20260912】')
        self.assertEqual(forum_draft._search_query(message), '基础数组求和题型作为参考')

    def test_workflow_status_is_removed_from_publishable_fields(self):
        draft = forum_draft._parse_draft(json.dumps({
            'post_type': 'tech', 'title': 'Python 技术说明',
            'summary': '这是一段足够长的有效技术摘要，说明文章内容。本文为草稿，暂不发布。',
            'content': '第一部分是有效的技术内容。以下内容为草稿整理，暂不发布。第二部分继续说明技术细节。',
            'resource_url': '',
        }, ensure_ascii=False), None)
        self.assertNotRegex(draft['summary'] + draft['content'], r'草稿|暂不发布')
        self.assertIn('第二部分继续说明技术细节', draft['content'])
