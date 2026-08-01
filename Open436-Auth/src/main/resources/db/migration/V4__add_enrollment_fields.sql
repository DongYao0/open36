-- 添加报名信息字段到用户认证表
-- 版本: v1.2

-- 1. 添加学号字段
ALTER TABLE users_auth ADD COLUMN IF NOT EXISTS student_id VARCHAR(30);

-- 2. 添加真实姓名字段
ALTER TABLE users_auth ADD COLUMN IF NOT EXISTS real_name VARCHAR(50);

-- 3. 添加电话号码字段
ALTER TABLE users_auth ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

-- 4. 添加专业字段
ALTER TABLE users_auth ADD COLUMN IF NOT EXISTS major VARCHAR(50);

-- 5. 添加注释
COMMENT ON COLUMN users_auth.student_id IS '学号';
COMMENT ON COLUMN users_auth.real_name IS '真实姓名';
COMMENT ON COLUMN users_auth.phone IS '电话号码';
COMMENT ON COLUMN users_auth.major IS '专业';

-- 6. 创建索引
CREATE INDEX IF NOT EXISTS idx_users_auth_student_id ON users_auth(student_id);
