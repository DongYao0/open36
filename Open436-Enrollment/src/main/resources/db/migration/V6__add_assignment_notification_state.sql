-- 作业表在旧环境中由 Hibernate 创建；全新环境会在 Flyway 后由 JPA 创建。
-- 因此迁移只处理已经存在的表，并保证可重复执行。
DO $$
BEGIN
    IF to_regclass('public.assignment_allocations') IS NOT NULL THEN
        ALTER TABLE assignment_allocations
            ADD COLUMN IF NOT EXISTS read_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS reminded_at TIMESTAMP;

        IF to_regclass('public.assignment_submissions') IS NOT NULL THEN
            -- 与旧版“已提交即已读”的可见行为兼容，未提交作业保持未读。
            UPDATE assignment_allocations a
               SET read_at = COALESCE(a.read_at, a.assigned_at)
             WHERE EXISTS (
                   SELECT 1 FROM assignment_submissions s
                    WHERE s.assignment_id = a.assignment_id
                      AND s.student_id = a.student_id
                      AND s.status = 'submitted'
             );
        END IF;

        CREATE INDEX IF NOT EXISTS idx_assignment_alloc_student_unread
            ON assignment_allocations (student_id, read_at);
    END IF;
END $$;
