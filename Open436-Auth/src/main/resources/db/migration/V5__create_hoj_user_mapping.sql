-- 创建 HOJ 用户映射表
-- 解决 Open436 与 HOJ 之间仅靠 username 关联的脆弱问题
-- 版本: v1.3

CREATE TABLE IF NOT EXISTS hoj_user_mapping (
    auth_user_id BIGINT PRIMARY KEY REFERENCES users_auth(id) ON DELETE CASCADE,
    hoj_uuid VARCHAR(32) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hoj_user_mapping IS 'Open436 与 HOJ 用户映射表';
COMMENT ON COLUMN hoj_user_mapping.auth_user_id IS 'Open436 用户ID（主键，外键）';
COMMENT ON COLUMN hoj_user_mapping.hoj_uuid IS 'HOJ 用户 UUID';
COMMENT ON COLUMN hoj_user_mapping.created_at IS '映射创建时间';

CREATE UNIQUE INDEX IF NOT EXISTS idx_hoj_mapping_auth_user ON hoj_user_mapping(auth_user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_hoj_mapping_hoj_uuid ON hoj_user_mapping(hoj_uuid);
