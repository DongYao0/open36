"""
自定义异常定义
"""


class AIServiceError(Exception):
    """AI服务基础异常"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


class AgentExecutionError(AIServiceError):
    """Agent执行异常"""
    def __init__(self, message: str):
        super().__init__(message, code=50001)


class LLMServiceError(AIServiceError):
    """LLM服务不可用"""
    def __init__(self, message: str = 'LLM服务不可用'):
        super().__init__(message, code=50301)


class ToolExecutionError(AIServiceError):
    """工具执行异常"""
    def __init__(self, tool_name: str, message: str):
        super().__init__(f'工具 {tool_name} 执行失败: {message}', code=50001)
