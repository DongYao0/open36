"""
Router Agent - 主路由Agent（意图识别与任务分发）
使用OpenAI兼容API（DeepSeek/Claude等）
"""
import json
import logging

from app.core.llm import llm

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """你是Open436平台的AI助手主路由。你的职责是理解用户的意图，并将其分发给对应的专业Agent处理。

意图分类规则：
1. chat - 日常对话、闲聊、问候、知识问答、计算类问题
2. forum - 论坛发帖。动作词：发帖/写帖子/发布帖子/创建帖子/create post
3. problem - 创建算法题。动作词：出题/创建题目/生成题目/改编题目/create problem/generate problem
4. search - 访问外部资源或爬取内容，包括：
   - 包含URL并要求获取/查看/展示其中的内容
   - 搜索/查找/爬取外部网站内容
   - 从洛谷/LeetCode/蓝桥云/Codeforces等平台查看题目
   - "帮我看看/给我看看/发给我看看" + 外部资源
5. query - 查询本平台内部数据（板块列表、任务状态、帖子列表等系统内部接口）
6. unclear - 纯表情、乱码、完全无法识别意图

判断优先级（按顺序匹配，先匹配到的优先）：
① 明确动作词（中英文均可）："发帖/create post" → forum，"出题/create problem/generate problem" → problem
② 包含URL 或 "爬取/搜索/找题/看看+外部资源" → search
③ 系统内部关键词："板块列表/任务状态/帖子列表" → query
④ 闲聊/问候/知识问答/计算 → chat
⑤ 其他 → unclear

关键区分：
- "看看" + 外部URL/外部平台 → search
- "看看" + 系统内部资源（板块、任务） → query
- 只要给了URL并要求获取内容 → search
- "蓝桥云/洛谷/LeetCode/Codeforces" + 题目 → search
- **复合意图**：当消息同时包含"搜索/找/搜"和"发帖/写帖子"时 → forum（forum agent会自动处理搜索）

示例：
- "帮我发个帖子" → forum
- "出一道二分查找题" → problem
- "https://xxx 帮我看看这个页面" → search
- "去蓝桥云搜索三道真题" → search
- "看看系统里有哪些板块" → query
- "你好" → chat
- "搜一篇关于AI的帖子并发帖" → forum（复合意图，forum会自动搜索）
- "找一篇Claude最新模型的帖子发到论坛" → forum
- "帮我搜集资料发个帖子" → forum

请只返回一个JSON对象，格式如下：
{"intent": "chat|forum|problem|search|query|unclear", "reason": "简短说明分类理由"}"""


async def classify_intent(user_message: str) -> dict:
    """
    使用LLM对用户消息进行意图分类

    Returns:
        {"intent": "forum|problem|query|unclear", "reason": "..."}
    """
    try:
        data = await llm.chat(
            messages=[
                {'role': 'system', 'content': ROUTER_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_message},
            ],
            temperature=0.3,
            max_tokens=256,
            timeout=30.0,
        )
        content = data['choices'][0]['message']['content'].strip()

        # 解析JSON
        if content.startswith('{'):
            result = json.loads(content)
        else:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {'intent': 'unclear', 'reason': '无法解析LLM响应'}

        valid_intents = {'chat', 'forum', 'problem', 'search', 'query', 'unclear'}
        if result.get('intent') not in valid_intents:
            result = {'intent': 'unclear', 'reason': '意图分类无效'}

        logger.info(f'意图分类: {result}')
        return result

    except Exception as e:
        logger.error(f'意图分类失败: {e}')
        return {'intent': 'unclear', 'reason': f'分类异常: {str(e)}'}
