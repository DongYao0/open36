-- M1 认证授权服务 - 添加客户端使用权限字段
-- 版本: v1.0

-- ============================================
-- 1. 在用户认证表添加客户端权限字段
-- ============================================
ALTER TABLE users_auth
    ADD COLUMN client_permission VARCHAR(20) NOT NULL DEFAULT 'all';

COMMENT ON COLUMN users_auth.client_permission IS '客户端使用权限: all-全部, forum-仅论坛, quiz-仅习题, none-无权限';

-- ============================================
-- 2. 添加索引
-- ============================================
CREATE INDEX idx_users_auth_client_permission ON users_auth(client_permission);

-- ============================================
-- 完成
-- ============================================
