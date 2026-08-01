-- V7: Create user profile and statistics tables (absorbed from UserService)

-- 1. User profile table
CREATE TABLE IF NOT EXISTS users_profile (
    user_id INTEGER PRIMARY KEY,
    nickname VARCHAR(20) NOT NULL,
    avatar_url VARCHAR(500),
    bio TEXT,
    nickname_updated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_nickname_length CHECK (LENGTH(nickname) >= 2 AND LENGTH(nickname) <= 20),
    CONSTRAINT chk_bio_length CHECK (bio IS NULL OR LENGTH(bio) <= 200)
);

COMMENT ON TABLE users_profile IS '用户资料表';
COMMENT ON COLUMN users_profile.user_id IS '用户ID（主键，关联 users_auth.id）';
COMMENT ON COLUMN users_profile.nickname IS '昵称（2-20字符）';
COMMENT ON COLUMN users_profile.avatar_url IS '头像URL（存储在文件服务）';
COMMENT ON COLUMN users_profile.bio IS '个人简介（最大200字符）';
COMMENT ON COLUMN users_profile.nickname_updated_at IS '昵称最后修改时间（用于30天限制）';

-- 2. User statistics table
CREATE TABLE IF NOT EXISTS user_statistics (
    user_id INTEGER PRIMARY KEY,
    posts_count INTEGER NOT NULL DEFAULT 0,
    replies_count INTEGER NOT NULL DEFAULT 0,
    likes_received INTEGER NOT NULL DEFAULT 0,
    favorites_received INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_stats_profile FOREIGN KEY (user_id)
        REFERENCES users_profile(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_posts_count CHECK (posts_count >= 0),
    CONSTRAINT chk_replies_count CHECK (replies_count >= 0),
    CONSTRAINT chk_likes_received CHECK (likes_received >= 0),
    CONSTRAINT chk_favorites_received CHECK (favorites_received >= 0)
);

COMMENT ON TABLE user_statistics IS '用户统计表';

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_users_profile_nickname ON users_profile(nickname);
CREATE INDEX IF NOT EXISTS idx_users_profile_created_at ON users_profile(created_at);
CREATE INDEX IF NOT EXISTS idx_user_statistics_posts_count ON user_statistics(posts_count DESC);
CREATE INDEX IF NOT EXISTS idx_user_statistics_likes_received ON user_statistics(likes_received DESC);

-- 4. Triggers for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_profile_updated_at ON users_profile;
CREATE TRIGGER update_users_profile_updated_at
    BEFORE UPDATE ON users_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_statistics_updated_at ON user_statistics;
CREATE TRIGGER update_user_statistics_updated_at
    BEFORE UPDATE ON user_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5. Migrate existing users: create profile for every existing auth user
INSERT INTO users_profile (user_id, nickname, created_at, updated_at)
SELECT id, '用户' || id, NOW(), NOW()
FROM users_auth
ON CONFLICT (user_id) DO NOTHING;

-- 6. Create statistics for every profile
INSERT INTO user_statistics (user_id, posts_count, replies_count, likes_received, favorites_received, updated_at)
SELECT user_id, 0, 0, 0, 0, NOW()
FROM users_profile
ON CONFLICT (user_id) DO NOTHING;
