"""
Orchestrator Agent - 理解任务→规划步骤→委派执行
替代原有的 Router 分类模式，支持多步骤复合任务。
"""
import json
import logging
import re

from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)

# ============== 旧版 Router（保留兼容） ==============

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

**重要区分 - "找题" vs "出题" vs "上传题"**：
- "找题/搜题/看题/查题/给我找题/我想看题" → search（用户想查看/搜索已有题目，不创建新题）
- "出题/创建题/生成题/出一道题/帮我生成" → problem（用户想创建新题目）
- "上传题/提交题/导入题/发布题到HOJ/把这道题上传/将这道题上传" → problem（用户想把题目提交到HOJ系统）
- "找两道二分查找的题" → search（搜索已有题目）
- "出一道二分查找的题" → problem（创建新题目）
- "将这道题上传到HOJ" → problem（提交题目）

示例：
- "帮我发个帖子" → forum
- "出一道二分查找题" → problem
- "找两道动态规划的题" → search（搜索已有题目）
- "给我看看二分查找的题目" → search
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
    旧版：使用LLM对用户消息进行意图分类（单标签）

    Returns:
        {"intent": "forum|problem|query|unclear", "reason": "..."}
    """
    try:
        msg = await get_chat_model(temperature=0.3, max_tokens=256).ainvoke([
            {'role': 'system', 'content': ROUTER_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message},
        ])
        content = msg.content.strip()

        if content.startswith('{'):
            result = json.loads(content)
        else:
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


# ============== 新版 Orchestrator（理解→规划→委派） ==============

ORCHESTRATOR_SYSTEM_PROMPT = """你是Open436平台的总指挥Orchestrator。你不是简单分类，而是深度理解用户需求，规划执行步骤，委派给专业Agent。

## 可用的专业Agent

| Agent | 能力 | 输入 |
|-------|------|------|
| search | 搜索外部资源、爬取网页、获取URL内容 | 搜索关键词或URL |
| forum | 生成论坛帖子并发布 | 帖子主题 + 参考素材 |
| problem | 生成算法题目 | 题目要求 + 参考素材 |
| chat | 日常对话、知识问答 | 用户消息 |
| query | 查询平台内部数据（板块、任务等） | 查询意图 |

## 规划原则

1. **理解真实意图**：不要只看关键词，要理解用户真正想要什么
   - "帮我找React Hooks教程发帖" → 用户要的是**帖子**，搜索只是手段
   - "看看这个URL" → 用户要的是**内容展示**，不需要发帖
   - "出一道二分查找题" → 用户要的是**创建新题目**
   - "找两道二分查找的题" → 用户要的是**搜索/查看已有题目**，不要创建

2. **"找题" vs "出题" vs "上传题" 区分（重要！）**：
   - "找题/搜题/看题/查题/给我找题/我想看题" → **search**（搜索已有题目，只看不创建）
   - "出题/创建题/生成题/出一道题/帮我生成" → **problem**（创建新题目并提交）
   - "上传题/提交题/导入题/发布题到HOJ/把这道题上传/将这道题上传" → **problem**（提交题目到HOJ）
   - "找两道动态规划的题" → search
   - "出一道动态规划的题" → problem
   - "将这道题上传到HOJ" → problem

2. **拆分必要步骤**：复合任务拆成多步，单步任务不要拆
   - "搜资料发帖" → [搜索, 写帖子] 两步
   - "帮我发个帖子" → [写帖子] 一步（forum agent自己决定是否需要搜索）
   - "看看这个URL" → [获取内容] 一步

3. **传递上下文**：后一步需要前一步的结果时，标记 `depends_on`
   - Step 1 搜索的结果 → Step 2 写帖子时需要参考

4. **简单任务不要过度拆分**：
   - "你好" → 直接 chat，不要拆
   - "帮我发个帖子" → 直接 forum，不要先搜索再写（forum agent自己会处理）

5. **时效性强制规则（最高优先级）**：
   分两类时效问题，路由不同：

   【A类·走 chat】纯系统时间问题（系统时钟已知，无需联网）：
   - 现在几点/今天星期几/今天日期/现在几月几日/今年是哪年
   - → chat（系统会注入当前时间，直接答）

   【B类·走 search】外部实时信息（必须联网）：
   - 版本/产品：最新模型/最新版本/XX出了什么/XX有什么新
   - 价格/数据：比特币价格/XX排名/XX排行榜
   - 事件动态：XX怎么样了/最近发生了什么
   - → search（强制联网，禁止用记忆）

   规则：B类问题即使一句话，也必须是 search，不准用 chat 凭记忆答。
   - "Claude最新模型是什么" → search（B类）
   - "现在几点" → chat（A类，系统知道时间）
   - "比特币现在多少钱" → search（B类）

## 输出格式

严格返回JSON，不要有其他内容：

```json
{
  "understanding": "用一句话描述用户真正想要什么",
  "steps": [
    {
      "step": 1,
      "agent": "search|forum|problem|chat|query",
      "task": "具体要做什么",
      "input": "传给这个agent的输入（如果是第一步，用用户原始消息；如果是后续步骤，说明依赖哪个step的结果）"
    }
  ],
  "reasoning": "为什么这样规划（一句话）"
}
```

## 示例

用户："搜一篇关于Vue3的教程发到论坛"
```json
{
  "understanding": "用户想搜索Vue3教程并发布到论坛",
  "steps": [
    {"step": 1, "agent": "search", "task": "搜索Vue3教程", "input": "Vue3 tutorial 2024"},
    {"step": 2, "agent": "forum", "task": "基于搜索结果写一篇论坛帖子", "input": "基于step 1的搜索结果，写一篇Vue3教程帖子"}
  ],
  "reasoning": "需要先搜索获取素材，再用素材写帖子"
}
```

用户："帮我发个帖子"
```json
{
  "understanding": "用户想发帖子，但没说具体内容",
  "steps": [
    {"step": 1, "agent": "forum", "task": "生成并发布帖子", "input": "帮我发个帖子"}
  ],
  "reasoning": "单步任务，forum agent会自己判断是否需要搜索"
}
```

用户："https://xxx.com/article 帮我看看"
```json
{
  "understanding": "用户想查看某个URL的内容",
  "steps": [
    {"step": 1, "agent": "search", "task": "获取URL内容并展示", "input": "https://xxx.com/article"}
  ],
  "reasoning": "只是查看内容，不需要发帖"
}
```

用户："你好"
```json
{
  "understanding": "用户在打招呼",
  "steps": [
    {"step": 1, "agent": "chat", "task": "日常对话", "input": "你好"}
  ],
  "reasoning": "简单对话，直接回复"
}
```

用户："找两道二分查找的题"
```json
{
  "understanding": "用户想搜索查看已有的二分查找题目",
  "steps": [
    {"step": 1, "agent": "search", "task": "搜索二分查找相关的算法题目", "input": "二分查找算法题"}
  ],
  "reasoning": "用户想看已有题目，不是创建新题"
}
```

用户："出一道二分查找的题"
```json
{
  "understanding": "用户想创建一道新的二分查找题目",
  "steps": [
    {"step": 1, "agent": "problem", "task": "生成二分查找算法题", "input": "出一道二分查找的题"}
  ],
  "reasoning": "用户要创建新题目，不是搜索已有的"
}
```"""


async def orchestrate(user_message: str) -> dict:
    """
    Orchestrator：理解任务 → 规划步骤 → 委派执行

    Returns:
        {
            "understanding": "用户想要什么",
            "steps": [{"step": 1, "agent": "forum", "task": "...", "input": "..."}],
            "reasoning": "为什么这样规划"
        }
    """
    try:
        msg = await get_chat_model(temperature=0.3, max_tokens=512).ainvoke([
            {'role': 'system', 'content': ORCHESTRATOR_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message},
        ])
        content = msg.content.strip()

        # 解析JSON（兼容markdown代码块）
        if '```' in content:
            content = re.sub(r'```json?\s*', '', content)
            content = content.replace('```', '').strip()

        if content.startswith('{'):
            result = json.loads(content)
        else:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = None

        if not result or 'steps' not in result:
            logger.warning(f'Orchestrator 返回格式异常: {content}')
            # fallback: 降级到旧版分类
            intent_result = await classify_intent(user_message)
            return {
                'understanding': intent_result.get('reason', ''),
                'steps': [{'step': 1, 'agent': intent_result['intent'], 'task': user_message, 'input': user_message}],
                'reasoning': f'降级到单步分类: {intent_result["intent"]}',
            }

        # 校验 agent 合法性
        valid_agents = {'chat', 'forum', 'problem', 'search', 'query', 'unclear'}
        for step in result['steps']:
            if step.get('agent') not in valid_agents:
                step['agent'] = 'chat'
                step['task'] = user_message

        logger.info(f'Orchestrator 规划: {result["understanding"]} → {len(result["steps"])} 步')
        return result

    except Exception as e:
        logger.error(f'Orchestrator 失败: {e}')
        return {
            'understanding': f'处理异常: {str(e)}',
            'steps': [{'step': 1, 'agent': 'unclear', 'task': user_message, 'input': user_message}],
            'reasoning': f'异常降级',
        }
