-- HOJ 原始初始化脚本包含历史演示 root 账号及未安装的本地语言运行时。
-- 此脚本在同一数据卷首次初始化时紧随 hoj.sql 执行，且重复执行仍安全。
USE `hoj`;

-- 仅记录公开题库统计的重置边界，不删除任何提交或判题明细。
CREATE TABLE IF NOT EXISTS `problem_stat_reset` (
  `pid` bigint(20) unsigned NOT NULL,
  `reset_submit_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `reset_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pid`),
  CONSTRAINT `problem_stat_reset_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `problem` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 公开提交列表按比赛/团队范围过滤后倒序分页；覆盖索引避免扫描、排序整张 judge 表。
SET @judge_public_list_index_sql = IF(
  EXISTS(SELECT 1 FROM information_schema.statistics
         WHERE table_schema = DATABASE() AND table_name = 'judge'
           AND index_name = 'idx_judge_public_list'),
  'SELECT 1',
  'ALTER TABLE `judge` ADD INDEX `idx_judge_public_list` (`cid`,`cpid`,`gid`,`submit_time` DESC,`submit_id` DESC)'
);
PREPARE judge_public_list_index_stmt FROM @judge_public_list_index_sql;
EXECUTE judge_public_list_index_stmt;
DEALLOCATE PREPARE judge_public_list_index_stmt;

-- 题目列表统计按 pid/cid/gid 聚合；包含 submit_id/status 后无需反复回表。
SET @judge_problem_stats_index_sql = IF(
  EXISTS(SELECT 1 FROM information_schema.statistics
         WHERE table_schema = DATABASE() AND table_name = 'judge'
           AND index_name = 'idx_judge_problem_stats'),
  'SELECT 1',
  'ALTER TABLE `judge` ADD INDEX `idx_judge_problem_stats` (`pid`,`cid`,`gid`,`submit_id`,`status`)'
);
PREPARE judge_problem_stats_index_stmt FROM @judge_problem_stats_index_sql;
EXECUTE judge_problem_stats_index_stmt;
DEALLOCATE PREPARE judge_problem_stats_index_stmt;

-- user_record / user_role 对 user_info 均为 ON DELETE CASCADE。
-- 第一个 Open436 admin 通过 /api/open436-sync 登录时会自动创建为 HOJ root 角色。
DELETE FROM `user_info` WHERE `uuid` = '1' AND `username` = 'root';

-- 只收紧本地判题语言；HDU/CF/POJ 等远程 OJ 语言定义不受影响。
DELETE FROM `language`
WHERE `oj` = 'ME'
  AND `name` NOT IN (
    'C', 'C With O2',
    'C++', 'C++ With O2',
    'C++ 17', 'C++ 17 With O2',
    'C++ 20', 'C++ 20 With O2',
    'Java', 'Python3', 'Golang', 'PHP', 'JavaScript Node', 'Ruby'
  );

-- 上游 seed 没有本地 Ruby 条目，但生产 Judge 与 go-judge 镜像均已支持。
INSERT INTO `language` (
  `content_type`, `description`, `name`, `compile_command`, `template`,
  `code_template`, `is_spj`, `oj`, `gmt_create`, `gmt_modified`
)
SELECT
  'text/x-ruby', 'Ruby', 'Ruby', '/usr/bin/ruby {src_path}',
  'a, b = STDIN.readline.split.map(&:to_i)\nputs a + b', NULL,
  0, 'ME', NOW(), NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM `language` WHERE `oj` = 'ME' AND `name` = 'Ruby'
);
