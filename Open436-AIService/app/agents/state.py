"""
LangGraph Agent 状态定义

AgentState 是主图 StateGraph 的状态 schema。
crawled_data / tool_calls / step_results 使用 operator.add reducer，
保证多步循环与子图并发时「累加」而非「覆盖」（复刻旧 run_agent 局部变量累加语义）。
"""
import operator
from typing import Annotated, TypedDict


class StepResult(TypedDict, total=False):
    """单步执行结果，供后续步骤前序注入参考"""
    step_index: int
    agent: str
    reply: str
    tool_calls: list[dict]
    token_usage: dict


class AgentState(TypedDict, total=False):
    # ===== 输入 =====
    user_message: str
    user_id: int
    history: list[dict]
    conversation_id: str

    # ===== 编排规划 =====
    understanding: str        # orchestrator 对用户意图的一句话理解
    plan: dict                # router.orchestrate 完整返回
    steps: list[dict]         # plan['steps']，每项 {step, agent, task, input}
    step_index: int           # 多步串行循环指针

    # ===== 累积数据（reducer: 追加）=====
    crawled_data: Annotated[list[dict], operator.add]
    tool_calls: Annotated[list[dict], operator.add]
    step_results: Annotated[list[StepResult], operator.add]

    # ===== 当前步输出 / 汇总 =====
    reply: str
    agent_name: str
    intent: str
    token_usage: dict
    total_tokens: dict

    # ===== 控制 =====
    cancelled: bool
