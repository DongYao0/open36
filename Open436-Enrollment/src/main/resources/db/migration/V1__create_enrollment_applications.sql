CREATE TABLE IF NOT EXISTS enrollment_applications (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(50),
    student_id VARCHAR(30),
    phone VARCHAR(20),
    major VARCHAR(50),
    self_intro TEXT,
    skills VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(50),
    review_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_enrollment_status ON enrollment_applications(status);
CREATE INDEX IF NOT EXISTS idx_enrollment_student_id ON enrollment_applications(student_id);
