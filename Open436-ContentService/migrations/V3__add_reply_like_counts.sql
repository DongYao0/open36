-- M3 帖子服务 - 添加回复数和点赞数计数字段

ALTER TABLE posts ADD COLUMN IF NOT EXISTS replies_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS likes_count INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN posts.replies_count IS '回复数（由M4评论服务同步更新）';
COMMENT ON COLUMN posts.likes_count IS '点赞数（由M4评论服务同步更新）';

CREATE INDEX IF NOT EXISTS idx_posts_likes ON posts(likes_count);
