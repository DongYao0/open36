-- 首页内容后台化管理：每模块一行，content 存 JSON
-- module: about | experiences | technologies | works | feedbacks
CREATE TABLE homepage_content (
    id BIGSERIAL PRIMARY KEY,
    module VARCHAR(50) NOT NULL UNIQUE,
    content JSON NOT NULL,
    updated_by BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 种子：实验室介绍（文本型，图片留空走前台 fallback）
INSERT INTO homepage_content (module, content) VALUES
('about', '{"subText":"实验室介绍","headText":"关于0436.","description":"0436 系统设计实验室专注前后端开发、智能计算与 AI 创新，为计算机专业学生提供系统化分层编程培训，拥有完善的前端、后端完整学习路线；实验室成员学业成绩优异，在挑战杯、计算机设计大赛、蓝桥杯等国家级赛事斩获多项一二三等奖；团队自主研发 Queue 学习平台、LeSoun AI 音乐创作等实战项目，还有多学科合作研发任务；实验室硬件配置顶配，配有独立服务器、双屏工位、打印机、冰箱与双中央空调，环境舒适；日常会组织聚餐、剧本杀等团建活动，学习氛围轻松互助，零基础同学也能得到学长学姐全程带教，欢迎热爱编程、竞赛、开发的同学加入 QQ 群了解纳新详情。","services":[{"title":"在线判题"},{"title":"编程赛事"},{"title":"技术社区"},{"title":"AI 助手"}]}'::jsonb);
