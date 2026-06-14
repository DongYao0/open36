-- 添加浏览角色
INSERT INTO roles (name, code, description) VALUES
('浏览用户', 'viewer', '仅可浏览论坛内容，不能发帖');

-- 分配浏览用户权限（只读）
INSERT INTO role_permissions (role_id, permission_id)
SELECT
    (SELECT id FROM roles WHERE code = 'viewer'),
    id
FROM permissions
WHERE code IN (
    'user:read'
);
