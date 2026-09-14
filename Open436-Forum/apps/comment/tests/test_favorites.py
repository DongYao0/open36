"""收藏边界行为测试。"""
from unittest.mock import patch

from django.db import connection
from django.test import override_settings
from rest_framework.test import APIRequestFactory, APITestCase

from apps.comment.models import PostFavorite
from apps.comment.views import InteractionViewSet


@override_settings(DATABASES={
    'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
})
class FavoriteCleanupTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, user_id)
                );
            """)

    @patch('apps.comment.views._update_user_stats')
    @patch('apps.comment.views._validate_post')
    def test_deleted_post_favorite_can_still_be_removed(self, validate_post, update_stats):
        favorite = PostFavorite.objects.create(post_id=404, user_id=7)
        request = APIRequestFactory().post('/api/comments/posts/404/favorite/')
        request.user_id = 7
        request.user_status = 'active'
        request.is_authenticated = True
        request.is_admin = False

        response = InteractionViewSet.as_view({'post': 'toggle_favorite'})(
            request, post_id=404
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['data']['is_favorited'])
        self.assertFalse(PostFavorite.objects.filter(id=favorite.id).exists())
        validate_post.assert_not_called()
        update_stats.assert_called_once_with(7, 'favorites_received', -1)
