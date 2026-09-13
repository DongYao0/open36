-- ─────────────────────────────────────────────────────────────
-- V10：注册幂等记录表（阶段5.2）
--
-- Auth 注册接口的幂等凭证：同一 X-Idempotency-Key 重复注册
-- 返回原用户；同 Key 不同内容返回 409。
-- 不存明文密码：request_fingerprint 只覆盖身份字段摘要。
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth_registration_records (
    id                  BIGSERIAL PRIMARY KEY,
    idempotency_key     VARCHAR(64)  NOT NULL,
    request_fingerprint VARCHAR(64)  NOT NULL,
    user_id             BIGINT,
    status              VARCHAR(20)  NOT NULL DEFAULT 'PROCESSING',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_auth_reg_idem_key
    ON auth_registration_records (idempotency_key);

CREATE INDEX IF NOT EXISTS idx_auth_reg_user_id
    ON auth_registration_records (user_id);
