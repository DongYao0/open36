-- Open436 用户管理扩展：客户端可见性。
-- 现有用户默认显示；脚本可安全重复执行。
SET @has_is_hidden = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'user_info'
    AND column_name = 'is_hidden'
);
SET @add_is_hidden = IF(
  @has_is_hidden = 0,
  'ALTER TABLE `user_info` ADD COLUMN `is_hidden` tinyint(1) NOT NULL DEFAULT 0 COMMENT ''是否在客户端排行榜隐藏：0显示，1隐藏'' AFTER `status`',
  'SELECT 1'
);
PREPARE add_is_hidden_stmt FROM @add_is_hidden;
EXECUTE add_is_hidden_stmt;
DEALLOCATE PREPARE add_is_hidden_stmt;
