-- 补齐 V7 之后由旧脚本或手工方式创建、但缺少资料记录的历史账号。
-- 正常应用创建链路仍由 UserProfileService#createProfileForUser 负责。

INSERT INTO users_profile (user_id, nickname, created_at, updated_at)
SELECT
    u.id,
    CASE
        WHEN LENGTH(COALESCE(NULLIF(BTRIM(u.real_name), ''), u.username)) BETWEEN 2 AND 20
            THEN COALESCE(NULLIF(BTRIM(u.real_name), ''), u.username)
        ELSE '用户' || u.id
    END,
    NOW(),
    NOW()
FROM users_auth u
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_statistics (
    user_id,
    posts_count,
    replies_count,
    likes_received,
    favorites_received,
    updated_at
)
SELECT p.user_id, 0, 0, 0, 0, NOW()
FROM users_profile p
ON CONFLICT (user_id) DO NOTHING;
