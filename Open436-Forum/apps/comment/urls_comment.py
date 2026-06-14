"""
Comment app URLs — 挂载在 /api/comments/ 下
前端通过 /api/comments/ 前缀访问互动功能
"""
from django.urls import path
from . import views

urlpatterns = [
    # 帖子互动（/api/comments/posts/{id}/...）
    path('posts/<int:post_id>/interaction-status/', views.InteractionViewSet.as_view({'get': 'interaction_status'}), name='interaction-status'),
    path('posts/<int:post_id>/like/', views.InteractionViewSet.as_view({'post': 'toggle_like'}), name='toggle-like'),
    path('posts/<int:post_id>/favorite/', views.InteractionViewSet.as_view({'post': 'toggle_favorite'}), name='toggle-favorite'),
    path('favorites/', views.InteractionViewSet.as_view({'get': 'my_favorites'}), name='my-favorites'),
    # 分享
    path('posts/<int:post_id>/share/', views.ShareViewSet.as_view({'post': 'record_share'}), name='record-share'),
    path('posts/<int:post_id>/share-count/', views.ShareViewSet.as_view({'get': 'share_count'}), name='share-count'),
    # 用户关注
    path('follows/users/<int:target_id>/toggle/', views.FollowViewSet.as_view({'post': 'toggle_follow'}), name='toggle-follow'),
    path('follows/users/<int:target_id>/status/', views.FollowViewSet.as_view({'get': 'follow_status'}), name='follow-status'),
    path('follows/my-following/', views.FollowViewSet.as_view({'get': 'my_following'}), name='my-following'),
    path('follows/my-followers/', views.FollowViewSet.as_view({'get': 'my_followers'}), name='my-followers'),
]
