-- 删除 Auth 用户时实时清理对应报名；报名删除后 interviews 由既有外键继续级联清理。
-- 先清理历史孤儿记录，否则无法建立外键约束。
DELETE FROM enrollment_applications enrollment
 WHERE enrollment.auth_user_id IS NULL
    OR NOT EXISTS (
        SELECT 1
          FROM users_auth auth_user
         WHERE auth_user.id = enrollment.auth_user_id
    );

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'fk_enrollment_auth_user'
           AND conrelid = 'enrollment_applications'::regclass
    ) THEN
        ALTER TABLE enrollment_applications
            ADD CONSTRAINT fk_enrollment_auth_user
            FOREIGN KEY (auth_user_id)
            REFERENCES users_auth(id)
            ON DELETE CASCADE;
    END IF;
END $$;
