-- 删除报名表中冗余的用户信息字段
-- 用户信息统一以 Auth 服务 users_auth 表为唯一可信源
-- 版本: v1.2

ALTER TABLE enrollment_applications
    DROP COLUMN IF EXISTS username,
    DROP COLUMN IF EXISTS password_hash,
    DROP COLUMN IF EXISTS real_name,
    DROP COLUMN IF EXISTS student_id,
    DROP COLUMN IF EXISTS phone,
    DROP COLUMN IF EXISTS major;

-- 原 username / student_id 索引不再需要
DROP INDEX IF EXISTS idx_enrollment_student_id;

-- 确保一个 Auth 用户只能有一条报名记录（PostgreSQL UNIQUE 允许多个 NULL，兼容历史数据）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uk_enrollment_auth_user_id'
        AND conrelid = 'enrollment_applications'::regclass
    ) THEN
        ALTER TABLE enrollment_applications
            ADD CONSTRAINT uk_enrollment_auth_user_id UNIQUE (auth_user_id);
    END IF;
END $$;
