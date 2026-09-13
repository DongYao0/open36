-- ─────────────────────────────────────────────────────────────
-- V4：论坛信息流组合索引（阶段4.4）
--
-- 现有索引全部单列，列表页实际查询模式为：
--   posts:   WHERE status=1 [AND section_id=?] ORDER BY is_pinned DESC, created_at DESC
--   replies: WHERE post_id=? AND is_deleted=false ORDER BY floor_number, created_at
--
-- 本文件幂等（IF NOT EXISTS），使用 CONCURRENTLY 避免锁表，
-- 直接对已有数据卷执行也安全（不能在事务块内运行）。
--
-- 全库扫描前后的 EXPLAIN ANALYZE 对比由
-- deploy/prod/scripts/upgrade-forum-indexes.sh 负责留存。
-- ─────────────────────────────────────────────────────────────

-- 公共帖子流（首页/全部板块）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_public_feed
    ON public.posts (status, is_pinned DESC, created_at DESC);

-- 分区帖子流（技术交流/资源分享各自列表）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_section_feed
    ON public.posts (section_id, status, is_pinned DESC, created_at DESC);

-- 帖子回复楼层翻页
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_replies_post_floor
    ON public.replies (post_id, is_deleted, floor_number);
