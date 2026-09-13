-- ─────────────────────────────────────────────────────────────
-- V5：报名链路幂等与状态机（阶段5.1/5.3）
--
-- processing_status 是"写入路径"状态机，与既有 status（审核态：
-- pending/approved/rejected）正交：
--
--   RECEIVED → CREATING_USER → USER_CREATED → PENDING(终态成功)
--        ↘ RETRYABLE_FAILED（网络超时等，同 Key 重试可恢复）
--        ↘ PERMANENT_FAILED（真实用户名冲突 / 幂等键内容漂移）
--
-- UNIQUE(idempotency_key) 是并发重复提交的最终防线；
-- UNIQUE(auth_user_id) 防跨 Key 重复报名。
-- 存量行 processing_status 置 PENDING（已是完成态）。
-- ─────────────────────────────────────────────────────────────
ALTER TABLE enrollment_applications
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(64),
    ADD COLUMN IF NOT EXISTS request_fingerprint VARCHAR(64),
    ADD COLUMN IF NOT EXISTS processing_status VARCHAR(30),
    ADD COLUMN IF NOT EXISTS last_error TEXT;

UPDATE enrollment_applications
   SET processing_status = 'PENDING'
 WHERE processing_status IS NULL;

ALTER TABLE enrollment_applications
    ALTER COLUMN processing_status SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_enroll_idem_key
    ON enrollment_applications (idempotency_key)
 WHERE idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_enroll_auth_user
    ON enrollment_applications (auth_user_id)
 WHERE auth_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_enroll_processing_stuck
    ON enrollment_applications (processing_status, submitted_at);
