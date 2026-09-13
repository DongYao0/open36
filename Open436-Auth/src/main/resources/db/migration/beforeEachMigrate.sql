-- V11 历史上把 homepage_content.content 创建为 json，而实体和 V13 按 jsonb 使用。
-- Flyway 回调会在每个版本迁移前执行；表尚未创建时无操作，V11 之后幂等转换。
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'homepage_content'
          AND column_name = 'content'
          AND data_type = 'json'
    ) THEN
        ALTER TABLE public.homepage_content
            ALTER COLUMN content TYPE jsonb
            USING content::jsonb;
    END IF;
END
$$;
