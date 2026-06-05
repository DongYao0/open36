"""
Problem Agent - 出题Agent（算法题生成）
Phase 2 完整实现，当前为占位
"""
import logging

logger = logging.getLogger(__name__)

PROBLEM_SYSTEM_PROMPT = """你是Open436平台的算法题出题Agent。你的职责是根据管理员的指令生成高质量的算法题目。

工作规范：
1. 题目描述清晰无歧义
2. 输入输出格式明确
3. 示例输入输出必须正确
4. 隐藏测试用例≥5组，覆盖边界情况
5. 参考解必须能通过所有测试用例
6. 难度标签与实际难度匹配"""


async def execute_problem_task(user_message: str, user_id: int) -> dict:
    """
    执行出题相关任务（Phase 2完整实现）

    当前返回占位响应，Phase 2将接入HOJ API
    """
    logger.warning('Problem Agent尚未完整实现（Phase 2）')
    return {
        'reply': '出题Agent正在开发中（Phase 2），敬请期待。当前支持的功能：论坛发帖、联网搜索。',
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }
