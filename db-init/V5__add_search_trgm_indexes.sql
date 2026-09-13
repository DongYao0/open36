-- ─────────────────────────────────────────────────────────────
-- V5：论坛搜索 pg_trgm GIN 索引（阶段4.5）
--
-- 现状：标题/摘要/正文 icontains 是全表扫描。第一阶段方案：
--   * 启用 pg_trgm，为 title / summary 建 GIN trigram 索引，
--     ilike 'xxx' 可走索引（不同 locale 下 icontains 翻译为 ILIKE）；
--   * 正文(content)暂不建索引（体积大、写放大明显），
--     应用层已限制搜索词长度与翻页深度（views.py 阶段4.5），
--     数据量上来后再升级 tsvector 全文检索。
--
-- 幂等：IF NOT EXISTS；CONCURRENTLY 避免锁表（不可在事务块内执行）。
-- ─────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_title_trgm
    ON public.posts USING gin (title gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_summary_trgm
    ON public.posts USING gin (summary gin_trgm_ops);
