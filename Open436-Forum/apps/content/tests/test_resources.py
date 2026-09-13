"""
/api/resources/ 接口测试 —— 必须真实路由到 ResourceViewSet，验证：
  - 列表接口返回 200 + 包含 share 板块帖子的 results
  - retrieve 接口返回 200 + Post 详情结构
  - section 过滤生效（只返回 share 板块）
"""
import pytest
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from django.db import connection

from apps.content.models import Post


@override_settings(DATABASES={
    'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
})
class ResourceViewSetTests(APITestCase):
    """测试 ResourceViewSet 路由与字段"""

    @classmethod
    def setUpTestData(cls):
        # Forum 表由 SQL 直建（Django managed=False），测试 setUp 中手工建表。
        # Schema 简化为与 production V1 一致。
        with connection.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(20) NOT NULL UNIQUE,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    color VARCHAR(7) NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 100,
                    is_enabled BOOLEAN NOT NULL DEFAULT 1,
                    posts_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(100) NOT NULL,
                    summary VARCHAR(300),
                    content TEXT NOT NULL,
                    author_id INTEGER NOT NULL,
                    is_ai_generated BOOLEAN NOT NULL DEFAULT 0,
                    section_id INTEGER NOT NULL,
                    is_pinned BOOLEAN NOT NULL DEFAULT 0,
                    pin_type VARCHAR(20) NOT NULL DEFAULT 'none',
                    views_count INTEGER NOT NULL DEFAULT 0,
                    replies_count INTEGER NOT NULL DEFAULT 0,
                    likes_count INTEGER NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'published',
                    edit_count INTEGER NOT NULL DEFAULT 0,
                    last_edited_at TIMESTAMP NULL,
                    last_edited_by INTEGER NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            c.execute("INSERT INTO sections (id, slug, name, color, sort_order) VALUES (1, 'share', '资源分享', '#00BCD4', 2)")
            c.execute("INSERT INTO sections (id, slug, name, color, sort_order) VALUES (2, 'tech', '技术交流', '#1976D2', 1)")

    def test_list_returns_share_section_only(self):
        # 创建 share 与 tech 各一帖
        Post.objects.create(id=1, title='R1', summary='', content='x',
                            author_id=100, section_id=1, status='published')
        Post.objects.create(id=2, title='R2', summary='', content='y',
                            author_id=100, section_id=2, status='published')

        resp = self.client.get('/api/resources/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        # 响应根级字段：code/message/timestamp/data，data 内 results
        self.assertEqual(body['code'], 200)
        results = body['data']['results']
        # 应当只包含 share 板块的帖子（id=1）
        ids = {p['id'] for p in results}
        self.assertIn(1, ids)
        self.assertNotIn(2, ids)

    def test_list_filter_by_author_id(self):
        Post.objects.create(id=10, title='A1', summary='', content='',
                            author_id=100, section_id=1, status='published')
        Post.objects.create(id=11, title='A2', summary='', content='',
                            author_id=200, section_id=1, status='published')

        resp = self.client.get('/api/resources/?author_id=200')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json()['data']['results']
        ids = {p['id'] for p in results}
        self.assertEqual(ids, {11})

    def test_list_pagination(self):
        # 创建 25 个资源，page_size=20
        for i in range(25):
            Post.objects.create(id=100 + i, title=f'R{i}', summary='', content='',
                                author_id=100, section_id=1, status='published')

        resp = self.client.get('/api/resources/?page_size=20&page=1')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertEqual(len(data['results']), 20)
        self.assertEqual(data['count'], 25)
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])

        # 第二页
        resp2 = self.client.get('/api/resources/?page_size=20&page=2')
        self.assertEqual(len(resp2.json()['data']['results']), 5)
        self.assertIsNone(resp2.json()['data']['next'])

    def test_retrieve_returns_post_detail(self):
        Post.objects.create(id=42, title='DetailTest', summary='简介',
                            content='内容', author_id=100, section_id=1,
                            status='published')
        resp = self.client.get('/api/resources/42/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        self.assertEqual(body['code'], 200)
        data = body['data']
        self.assertEqual(data['id'], 42)
        self.assertEqual(data['title'], 'DetailTest')
        # PostDetailSerializer 输出 author 是嵌套 dict {user_id, nickname, avatar_url}
        self.assertEqual(data['author']['user_id'], 100)
        # section 嵌套 dict
        self.assertEqual(data['section']['slug'], 'share')

    def test_retrieve_404_for_non_resource(self):
        # tech 板块帖子不应通过 /api/resources/ 检索到
        Post.objects.create(id=99, title='Tech', summary='', content='',
                            author_id=100, section_id=2, status='published')
        resp = self.client.get('/api/resources/99/')
        # ResourceViewSet.queryset 已过滤 section__slug='share'，tech 帖子不在结果集
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_404_for_missing(self):
        resp = self.client.get('/api/resources/9999/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)