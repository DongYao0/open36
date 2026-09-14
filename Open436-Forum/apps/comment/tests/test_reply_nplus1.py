"""
阶段4.3验收：回复列表 N+1 查询消除。

要求：1 条回复与 50 条回复的 SQL 数量基本稳定，不随回复数线性增加。
改造后列表 = 1 次 COUNT + 1 次 SELECT（点赞数/是否点赞走注解）。
"""
from django.db import connection
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import call, patch

from apps.comment.models import Reply, ReplyLike


@override_settings(DATABASES={
    'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
})
class ReplyListQueryCountTests(APITestCase):
    """回复列表 SQL 数量不随回复数线性增长"""

    @classmethod
    def setUpTestData(cls):
        # Forum 表由 SQL 直建（Django managed=False），测试手工建表
        with connection.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    parent_id INTEGER,
                    content TEXT NOT NULL,
                    floor_number INTEGER NOT NULL,
                    is_deleted BOOLEAN NOT NULL DEFAULT 0,
                    edit_count INTEGER NOT NULL DEFAULT 0,
                    last_edited_at TIMESTAMP NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS reply_likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reply_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def _create_replies(self, n):
        Reply.objects.bulk_create([
            Reply(post_id=1, author_id=100 + (i % 5), content=f'reply-{i}',
                  floor_number=i + 1)
            for i in range(n)
        ])

    def test_query_count_stable_from_1_to_50_replies(self):
        self._create_replies(1)
        with self.assertNumQueries(2) as one:
            resp = self.client.get('/api/replies/?post_id=1')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()['data']['results']), 1)
        baseline = len(one)

        self._create_replies(49)  # 共 50 条
        with self.assertNumQueries(baseline) as many:
            resp = self.client.get('/api/replies/?post_id=1')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()['data']['results']), 50)
        self.assertEqual(len(many), baseline,
                         '回复数从 1→50 时 SQL 数量不得增长（N+1 已消除）')

    def test_likes_count_and_is_liked_annotated(self):
        self._create_replies(5)
        ReplyLike.objects.bulk_create([
            ReplyLike(reply_id=i + 1, user_id=999) for i in range(5)
        ])
        with self.assertNumQueries(2):
            resp = self.client.get('/api/replies/?post_id=1')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json()['data']['results']
        self.assertTrue(all(r['likes_count'] == 1 for r in results))
        # 匿名请求：is_liked 恒 False，且不产生逐条查询
        self.assertTrue(all(r['is_liked'] is False for r in results))

    def test_invalid_pagination_params_return_400(self):
        for bad in ['?post_id=1&page=abc', '?post_id=1&page_size=xyz',
                    '?post_id=1&page=0', '?post_id=1&page_size=-1']:
            resp = self.client.get(f'/api/replies/{bad}')
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST,
                             f'{bad} 应返回 400 而非 500')

    @patch('apps.comment.views.get_author_profiles')
    def test_reply_author_uses_real_name_and_avatar(self, profiles):
        self._create_replies(1)
        profiles.return_value = {
            100: {
                'real_name': '张三',
                'nickname': 'nickname-only-fallback',
                'avatar_url': '/objects/open436-posts/avatar.jpg',
            }
        }

        resp = self.client.get('/api/replies/?post_id=1')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        author = resp.json()['data']['results'][0]['author']
        self.assertEqual(author['nickname'], '张三')
        self.assertEqual(author['real_name'], '张三')
        self.assertEqual(author['avatar_url'], '/objects/open436-posts/avatar.jpg')

    @patch('apps.core.middleware._get_verified_user')
    def test_user_filter_returns_only_current_users_replies(self, verified_user):
        verified_user.return_value = {
            'user_id': 100, 'username': 'u100', 'role': 'user', 'status': 'active'
        }
        Reply.objects.bulk_create([
            Reply(post_id=1, author_id=100, content='mine', floor_number=1),
            Reply(post_id=1, author_id=200, content='other', floor_number=2),
        ])

        resp = self.client.get('/api/replies/?user_id=100', HTTP_TOKEN='mine-token')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json()['data']['results']
        self.assertEqual([item['author']['user_id'] for item in results], [100])

    @patch('apps.core.middleware._get_verified_user')
    def test_user_filter_rejects_other_users_replies(self, verified_user):
        verified_user.return_value = {
            'user_id': 100, 'username': 'u100', 'role': 'user', 'status': 'active'
        }

        resp = self.client.get('/api/replies/?user_id=200', HTTP_TOKEN='mine-token')

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_reply_is_hidden_from_public_list(self):
        Reply.objects.create(post_id=1, author_id=100, content='deleted',
                             floor_number=1, is_deleted=True)
        resp = self.client.get('/api/replies/?post_id=1')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['results'], [])

    @patch('apps.comment.views._update_post_count')
    @patch('apps.comment.views._update_user_stats')
    @patch('apps.comment.views._validate_post', return_value=(True, None))
    @patch('apps.core.middleware._get_verified_user')
    def test_third_level_reply_can_target_second_level_reply(
            self, verified_user, _validate, _user_stats, _post_count):
        verified_user.return_value = {
            'user_id': 100, 'username': 'u100', 'role': 'user', 'status': 'active'
        }
        root = Reply.objects.create(
            post_id=1, author_id=200, content='root', floor_number=1)
        second = Reply.objects.create(
            post_id=1, author_id=300, parent_id=root.id,
            content='second', floor_number=2)

        resp = self.client.post(
            '/api/replies/',
            {'post_id': 1, 'parent_id': second.id, 'content': 'third level'},
            format='json', HTTP_TOKEN='third-level-token')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        created = Reply.objects.get(id=resp.json()['data']['id'])
        self.assertEqual(created.parent_id, second.id)

    @patch('apps.comment.views._update_post_count')
    @patch('apps.comment.views._update_user_stats')
    @patch('apps.core.middleware._get_verified_user')
    def test_deleting_root_cascades_to_all_descendants(
            self, verified_user, user_stats, post_count):
        verified_user.return_value = {
            'user_id': 100, 'username': 'u100', 'role': 'user', 'status': 'active'
        }
        root = Reply.objects.create(
            post_id=1, author_id=100, content='root', floor_number=1)
        child = Reply.objects.create(
            post_id=1, author_id=200, parent_id=root.id,
            content='child', floor_number=2)
        grandchild = Reply.objects.create(
            post_id=1, author_id=300, parent_id=child.id,
            content='grandchild', floor_number=3)
        sibling_root = Reply.objects.create(
            post_id=1, author_id=400, content='keep me', floor_number=4)

        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.delete(
                f'/api/replies/{root.id}/', HTTP_TOKEN='owner-token')
            repeated_resp = self.client.delete(
                f'/api/replies/{root.id}/', HTTP_TOKEN='owner-token')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(repeated_resp.status_code, status.HTTP_200_OK)
        deleted = Reply.objects.filter(
            id__in=[root.id, child.id, grandchild.id], is_deleted=True
        ).count()
        self.assertEqual(deleted, 3)
        sibling_root.refresh_from_db()
        self.assertFalse(sibling_root.is_deleted)
        post_count.assert_called_once_with(1, 'increment-replies', -3)
        user_stats.assert_has_calls([
            call(100, 'replies_count', -1),
            call(200, 'replies_count', -1),
            call(300, 'replies_count', -1),
        ], any_order=True)
