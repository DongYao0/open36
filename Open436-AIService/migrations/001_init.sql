-- M8 AI智能服务 数据库初始化脚本
-- 数据库: ai_db

-- 会话表
CREATE TABLE IF NOT EXISTS ai_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 消息表
CREATE TABLE IF NOT EXISTS ai_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    intent VARCHAR(50),
    agent_name VARCHAR(50),
    token_usage JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 异步任务表
CREATE TABLE IF NOT EXISTS ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    conversation_id UUID REFERENCES ai_conversations(id) ON DELETE SET NULL,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    input_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    agent_name VARCHAR(50) NOT NULL,
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 工具调用记录表
CREATE TABLE IF NOT EXISTS ai_tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES ai_messages(id) ON DELETE CASCADE,
    task_id UUID REFERENCES ai_tasks(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    tool_input JSONB NOT NULL,
    tool_output JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed')),
    error_message TEXT,
    duration_ms INT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Agent配置表
CREATE TABLE IF NOT EXISTS ai_agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    temperature DECIMAL(3,2) NOT NULL DEFAULT 0.70,
    max_tokens INT NOT NULL DEFAULT 4096,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 文档元数据表
CREATE TABLE IF NOT EXISTS ai_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size BIGINT NOT NULL,
    chunk_count INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON ai_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON ai_conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON ai_conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON ai_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON ai_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON ai_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON ai_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON ai_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON ai_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON ai_tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tool_calls_message_id ON ai_tool_calls(message_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_task_id ON ai_tool_calls(task_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_created_at ON ai_tool_calls(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_configs_name ON ai_agent_configs(agent_name);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON ai_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON ai_documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON ai_documents(created_at DESC);

-- 预置Agent配置
INSERT INTO ai_agent_configs (agent_name, display_name, model, system_prompt, temperature, max_tokens) VALUES
('router', '主路由Agent', 'claude-sonnet-4-20250514', '你是Open436平台的AI助手主路由。你的职责是理解管理员的意图，并将其分发给对应的专业Agent处理。

意图分类规则：
1. forum - 论坛相关（发帖、编辑帖子、查看帖子）
2. problem - 出题相关（创建算法题、生成测试用例）
3. query - 查询相关（查看板块列表、查看任务状态）
4. unclear - 无法识别，需要澄清

请根据用户输入返回JSON格式的意图分类。', 0.3, 1024),

('forum', '论坛Agent', 'claude-sonnet-4-20250514', '你是Open436平台的论坛内容管理Agent。你的职责是根据管理员的指令创建、编辑论坛帖子。

工作规范：
1. 帖子内容使用Markdown格式
2. 技术内容必须准确，代码示例必须可运行
3. 标题简洁有吸引力，5-100字符
4. 内容充实有结构，500-5000字
5. 使用合适的标题、列表、代码块等格式化元素
6. 涉及时效性内容（如"最新"、"近期"）时，先使用search_web搜索最新信息再生成内容

你可以使用以下工具：
- search_web: 联网搜索最新信息
- fetch_url: 抓取网页内容
- create_post: 创建帖子
- list_sections: 获取板块列表
- list_posts: 查看帖子列表
- update_post: 编辑帖子', 0.7, 8192),

('problem', '出题Agent', 'claude-sonnet-4-20250514', '你是Open436平台的算法题出题Agent。你的职责是根据管理员的指令生成高质量的算法题目。

工作规范：
1. 题目描述清晰无歧义
2. 输入输出格式明确
3. 示例输入输出必须正确
4. 隐藏测试用例≥5组，覆盖边界情况
5. 参考解必须能通过所有测试用例
6. 难度标签与实际难度匹配

你可以使用以下工具：
- create_problem: 创建题目到HOJ系统
- generate_examples: 生成示例输入输出
- generate_testcases: 生成隐藏测试用例
- generate_solution: 生成参考解题代码', 0.5, 8192)

ON CONFLICT (agent_name) DO NOTHING;
