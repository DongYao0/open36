-- Mark posts created through the AI forum workflow.
-- IF NOT EXISTS keeps this safe for both upgraded and newly initialized databases.
ALTER TABLE public.posts
    ADD COLUMN IF NOT EXISTS is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_posts_is_ai_generated
    ON public.posts (is_ai_generated);
