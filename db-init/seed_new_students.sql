-- ============================================
-- 新增学生种子数据 - 报名管理 & 面试管理
-- 生成日期: 2026-08-01
-- ============================================

-- ============================================
-- 0. 新增管理员账号
-- ============================================
-- 密码: Open436@2024
INSERT INTO users_auth (username, password_hash, status, client_permission, created_at, updated_at) VALUES
('open436admin', '$2b$10$V0nZBmjdLq/hx5oGcIFLduTOi0Gv8JHvP2UHYCsS0jU98HhZw8LFe', 'active', 'all', NOW(), NOW())
ON CONFLICT (username) DO NOTHING;

-- 分配管理员角色
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE code = 'admin')
FROM users_auth u
WHERE u.username = 'open436admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = (SELECT id FROM roles WHERE code = 'admin')
  );

-- ============================================
-- 1. 插入3个新学生用户 (users_auth)
-- ============================================
-- 密码: student123
INSERT INTO users_auth (username, password_hash, status, student_id, real_name, phone, major, client_permission, created_at, updated_at) VALUES
('zhaohaoran', '$2b$10$hczvK0jbrzxLhUIv4wICfOMu21G1zKQxItWRoGGH6Dm3Fja4RCNXa', 'active', '20240201001', '赵浩然', '13900002001', '数据科学与大数据技术', 'all', NOW(), NOW()),
('liuyutong',  '$2b$10$hczvK0jbrzxLhUIv4wICfOMu21G1zKQxItWRoGGH6Dm3Fja4RCNXa', 'active', '20240201002', '刘雨桐', '13900002002', '网络安全',           'all', NOW(), NOW()),
('sunwenbo',   '$2b$10$hczvK0jbrzxLhUIv4wICfOMu21G1zKQxItWRoGGH6Dm3Fja4RCNXa', 'active', '20240201003', '孙文博', '13900002003', '电子信息工程',       'all', NOW(), NOW())
ON CONFLICT (username) DO NOTHING;

-- 分配普通用户角色
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE code = 'user')
FROM users_auth u
WHERE u.username IN ('zhaohaoran', 'liuyutong', 'sunwenbo')
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = (SELECT id FROM roles WHERE code = 'user')
  );

-- ============================================
-- 2. 插入报名数据 (enrollment_applications)
-- ============================================

-- 赵浩然 - 待审核 (pending)
INSERT INTO enrollment_applications (auth_user_id, self_intro, skills, status, submitted_at) VALUES
(
    (SELECT id FROM users_auth WHERE username = 'zhaohaoran'),
    '大二学生，对大数据处理和数据挖掘方向感兴趣，自学了Hadoop和Spark基础，参加过数学建模竞赛并获得省级三等奖，希望加入Open436团队提升工程实践能力。',
    'Python, SQL, Hadoop, Spark, Data Analysis, Excel',
    'pending',
    '2026-07-28 15:20:00'
);

-- 刘雨桐 - 已通过 (approved)
INSERT INTO enrollment_applications (auth_user_id, self_intro, skills, status, submitted_at, reviewed_at, reviewed_by, review_reason) VALUES
(
    (SELECT id FROM users_auth WHERE username = 'liuyutong'),
    '大三学生，CTF战队成员，擅长Web安全和渗透测试，参加过全国大学生信息安全竞赛并获得二等奖，熟悉常见的Web漏洞攻防技术，希望加入团队的安全方向。',
    'Python, Burp Suite, Wireshark, Kali Linux, Docker, Go',
    'approved',
    '2026-07-25 10:30:00',
    '2026-07-26 16:00:00',
    'admin',
    '安全方向能力突出，CTF竞赛经验丰富，是社团需要的安全人才。'
);

-- 孙文博 - 已通过 (approved)
INSERT INTO enrollment_applications (auth_user_id, self_intro, skills, status, submitted_at, reviewed_at, reviewed_by, review_reason) VALUES
(
    (SELECT id FROM users_auth WHERE username = 'sunwenbo'),
    '大二学生，热爱嵌入式开发和IoT，参加过电赛和智能车竞赛，熟悉STM32和Arduino开发，有一定的PCB设计经验，希望通过Open436拓展软件开发能力。',
    'C, C++, STM32, Arduino, PCB Design, Linux, Python',
    'approved',
    '2026-07-26 08:45:00',
    '2026-07-27 14:30:00',
    'admin',
    '硬件基础扎实，有实际项目经验，可以在软硬件结合方向发挥作用。'
);

-- ============================================
-- 3. 插入面试数据 (interviews)
-- ============================================

-- 赵浩然 - 面试待安排 (pending)
INSERT INTO interviews (enrollment_id, auth_user_id, status, round, created_at, updated_at)
SELECT
    ea.id,
    u.id,
    'pending',
    1,
    NOW(), NOW()
FROM enrollment_applications ea
JOIN users_auth u ON ea.auth_user_id = u.id
WHERE u.username = 'zhaohaoran'
  AND NOT EXISTS (SELECT 1 FROM interviews WHERE auth_user_id = u.id);

-- 刘雨桐 - 面试已通过 (passed)
INSERT INTO interviews (enrollment_id, auth_user_id, status, round, interview_date, interviewer, score, summary, strengths, weaknesses, direction, created_at, updated_at)
SELECT
    ea.id,
    u.id,
    'passed',
    1,
    '2026-07-28 09:30:00',
    '王老师',
    9,
    '安全意识强，对Web漏洞原理理解深入，展示了自己挖掘的多个SRC漏洞案例，思维敏捷，沟通表达流畅。',
    'Web安全技术扎实，漏洞挖掘经验丰富，学习能力强，有团队分享精神。',
    '对移动端安全和二进制方向涉猎较少，可适当拓宽安全视野。',
    '安全方向',
    NOW(), NOW()
FROM enrollment_applications ea
JOIN users_auth u ON ea.auth_user_id = u.id
WHERE u.username = 'liuyutong'
  AND NOT EXISTS (SELECT 1 FROM interviews WHERE auth_user_id = u.id);

-- 孙文博 - 面试未通过 (failed)
INSERT INTO interviews (enrollment_id, auth_user_id, status, round, interview_date, interviewer, score, summary, strengths, weaknesses, direction, created_at, updated_at)
SELECT
    ea.id,
    u.id,
    'failed',
    1,
    '2026-07-29 14:00:00',
    '张老师',
    5,
    '硬件能力不错，但软件开发基础较弱，对数据结构和算法的掌握不够扎实，代码能力有待提升，建议先加强编程基础后再申请。',
    '硬件开发经验丰富，动手能力强，对嵌入式有热情。',
    '软件基础薄弱，算法和数据结构掌握不足，缺乏Web开发相关知识。',
    '待定',
    NOW(), NOW()
FROM enrollment_applications ea
JOIN users_auth u ON ea.auth_user_id = u.id
WHERE u.username = 'sunwenbo'
  AND NOT EXISTS (SELECT 1 FROM interviews WHERE auth_user_id = u.id);

-- ============================================
-- 4. 更新序列值
-- ============================================
SELECT setval('users_auth_id_seq', GREATEST((SELECT COALESCE(MAX(id), 0) FROM users_auth), 1));
SELECT setval('enrollment_applications_id_seq', GREATEST((SELECT COALESCE(MAX(id), 0) FROM enrollment_applications), 1));
SELECT setval('interviews_id_seq', GREATEST((SELECT COALESCE(MAX(id), 0) FROM interviews), 1));

-- ============================================
-- 完成
-- ============================================
-- 管理员: open436admin / Open436@2024
-- 学生1: 赵浩然 (zhaohaoran) - 20240201001 - 数据科学与大数据技术 - 报名待审核 - 面试待安排
-- 学生2: 刘雨桐 (liuyutong) - 20240201002 - 网络安全           - 报名已通过 - 面试已通过
-- 学生3: 孙文博 (sunwenbo)   - 20240201003 - 电子信息工程       - 报名已通过 - 面试未通过
-- 学生默认密码: student123
