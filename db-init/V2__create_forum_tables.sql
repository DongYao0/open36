-- =====================================================
-- Open436 Forum 服务 - 数据库迁移脚本
-- 版本: V2
-- 创建日期: 2026-08-01
-- 说明: 创建帖子 / 评论 / 互动等表（content + comment 模块）
-- 注意: Django 模型中这些表均为 managed=False，需由 SQL 直接创建
--       （对应 Open436-Forum/apps/content、apps/comment 的模型定义）
-- =====================================================

-- 1. 帖子表 posts
CREATE TABLE IF NOT EXISTS public.posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    summary VARCHAR(300),
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    pin_type VARCHAR(20) NOT NULL DEFAULT 'none',
    views_count INTEGER NOT NULL DEFAULT 0,
    replies_count INTEGER NOT NULL DEFAULT 0,
    likes_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'published',
    edit_count INTEGER NOT NULL DEFAULT 0,
    last_edited_at TIMESTAMPTZ,
    last_edited_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_posts_section_id ON public.posts (section_id);
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON public.posts (author_id);
CREATE INDEX IF NOT EXISTS idx_posts_is_pinned ON public.posts (is_pinned);
CREATE INDEX IF NOT EXISTS idx_posts_pin_type ON public.posts (pin_type);
CREATE INDEX IF NOT EXISTS idx_posts_status ON public.posts (status);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts (created_at DESC);

-- 2. 帖子编辑历史 post_edit_history
CREATE TABLE IF NOT EXISTS public.post_edit_history (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    section_id INTEGER NOT NULL,
    edited_by INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_post_edit_history_post_id ON public.post_edit_history (post_id);

-- 3. 回复表 replies
CREATE TABLE IF NOT EXISTS public.replies (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    parent_id INTEGER,
    content TEXT NOT NULL,
    floor_number INTEGER NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    edit_count INTEGER NOT NULL DEFAULT 0,
    last_edited_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_replies_post_id ON public.replies (post_id);
CREATE INDEX IF NOT EXISTS idx_replies_author_id ON public.replies (author_id);
CREATE INDEX IF NOT EXISTS idx_replies_parent_id ON public.replies (parent_id);
CREATE INDEX IF NOT EXISTS idx_replies_is_deleted ON public.replies (is_deleted);

-- 4. 帖子点赞 post_likes
CREATE TABLE IF NOT EXISTS public.post_likes (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON public.post_likes (post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON public.post_likes (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_post_likes_post_user ON public.post_likes (post_id, user_id);

-- 5. 帖子收藏 post_favorites
CREATE TABLE IF NOT EXISTS public.post_favorites (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_post_favorites_post_id ON public.post_favorites (post_id);
CREATE INDEX IF NOT EXISTS idx_post_favorites_user_id ON public.post_favorites (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_post_favorites_post_user ON public.post_favorites (post_id, user_id);

-- 6. 评论点赞 reply_likes
CREATE TABLE IF NOT EXISTS public.reply_likes (
    id SERIAL PRIMARY KEY,
    reply_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_reply_likes_reply_id ON public.reply_likes (reply_id);
CREATE INDEX IF NOT EXISTS idx_reply_likes_user_id ON public.reply_likes (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_reply_likes_reply_user ON public.reply_likes (reply_id, user_id);

-- 7. 分享记录 share_records
CREATE TABLE IF NOT EXISTS public.share_records (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER,
    share_type VARCHAR(20) NOT NULL DEFAULT 'link',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_share_records_post_id ON public.share_records (post_id);
CREATE INDEX IF NOT EXISTS idx_share_records_user_id ON public.share_records (user_id);

-- 8. 用户关注 user_follows
CREATE TABLE IF NOT EXISTS public.user_follows (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER NOT NULL,
    following_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_user_follows_follower_id ON public.user_follows (follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following_id ON public.user_follows (following_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_follows_pair ON public.user_follows (follower_id, following_id);

-- 9. 话题 topics
CREATE TABLE IF NOT EXISTS public.topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200) NOT NULL DEFAULT '',
    posts_count INTEGER NOT NULL DEFAULT 0,
    followers_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 10. 话题关注 topic_follows
CREATE TABLE IF NOT EXISTS public.topic_follows (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_topic_follows_user_id ON public.topic_follows (user_id);
CREATE INDEX IF NOT EXISTS idx_topic_follows_topic_id ON public.topic_follows (topic_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_topic_follows_user_topic ON public.topic_follows (user_id, topic_id);
