-- 放宽 username 最小长度：3 -> 2
-- 报名以真实姓名作为登录账号，需兼容 2 字姓名（如「张三」）
-- 对应 Java 侧 LoginRequest/RegisterRequest/CreateUserRequest/ApplyRequest 的 @Size(min=2)
ALTER TABLE users_auth DROP CONSTRAINT IF EXISTS chk_username_length;
ALTER TABLE users_auth ADD CONSTRAINT chk_username_length CHECK (LENGTH(username) >= 2);
