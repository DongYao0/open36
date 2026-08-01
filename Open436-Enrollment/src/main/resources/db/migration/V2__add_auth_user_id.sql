-- 添加 auth_user_id 字段到报名表，关联 users_auth.id
-- 版本: v1.1

ALTER TABLE enrollment_applications ADD COLUMN IF NOT EXISTS auth_user_id BIGINT;

COMMENT ON COLUMN enrollment_applications.auth_user_id IS '关联 Auth 服务的 users_auth.id';

CREATE INDEX IF NOT EXISTS idx_enrollment_auth_user_id ON enrollment_applications(auth_user_id);
