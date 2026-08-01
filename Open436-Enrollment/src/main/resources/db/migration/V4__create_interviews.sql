-- 面试管理表
-- 关联报名申请与面试记录，一个报名申请可有多轮面试

CREATE TABLE IF NOT EXISTS interviews (
    id BIGSERIAL PRIMARY KEY,
    enrollment_id BIGINT NOT NULL,
    auth_user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    round INTEGER NOT NULL DEFAULT 1,
    interview_date TIMESTAMP,
    interviewer VARCHAR(50),
    score INTEGER,
    summary TEXT,
    strengths TEXT,
    weaknesses TEXT,
    direction VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_interview_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollment_applications(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interview_enrollment_id ON interviews(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_interview_auth_user_id ON interviews(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_interview_status ON interviews(status);

COMMENT ON TABLE interviews IS '面试记录表';
COMMENT ON COLUMN interviews.enrollment_id IS '关联报名申请ID';
COMMENT ON COLUMN interviews.auth_user_id IS '关联Auth服务用户ID';
COMMENT ON COLUMN interviews.status IS '面试状态: pending/interviewed/passed/failed';
COMMENT ON COLUMN interviews.round IS '面试轮次';
COMMENT ON COLUMN interviews.interviewer IS '面试官';
COMMENT ON COLUMN interviews.score IS '面试评分(1-10)';
COMMENT ON COLUMN interviews.summary IS '面试总结';
COMMENT ON COLUMN interviews.direction IS '推荐方向';
