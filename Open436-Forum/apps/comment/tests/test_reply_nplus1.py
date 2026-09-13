"""
阶段4.3验收：回复列表 N+1 查询消除。

要求：1 条回复与 50 条回复的 SQL 数量基本稳定，不随回复数线性增加。
改造后列表 = 1 次 COUNT + 1 次 SELECT（点赞数/是否点赞走注解）。
"""
from django.db import connection
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

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
