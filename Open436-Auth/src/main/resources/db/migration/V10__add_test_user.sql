-- 添加测试账号
-- 密码: 111111
-- 注意：测试账号用户名 'a' 仅 1 字符，先放宽 V9 设立的长度约束(>=2 -> >=1)
ALTER TABLE users_auth DROP CONSTRAINT IF EXISTS chk_username_length;
ALTER TABLE users_auth ADD CONSTRAINT chk_username_length CHECK (LENGTH(username) >= 1);

INSERT INTO users_auth (username, password_hash, status, client_permission, created_at, updated_at) VALUES
('a', '$2a$10$XOw4a2HbXjVnHKtsw4z70uYTRz.5js7o7lelFdgvblds7eoVyEsUC', 'active', 'all', NOW(), NOW())
ON CONFLICT (username) DO NOTHING;

-- 分配普通用户角色
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE code = 'user')
FROM users_auth u
WHERE u.username = 'a'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = (SELECT id FROM roles WHERE code = 'user')
  );
