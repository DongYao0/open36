"""
统一响应格式（与现有Python服务一致）
"""
import time


def success_response(data=None, message='success', code=200):
    """成功响应"""
    response = {
        'code': code,
        'message': message,
        'timestamp': int(time.time() * 1000),
    }
    if data is not None:
        response['data'] = data
    return response


def error_response(message, code=400, errors=None, status_code=400):
    """错误响应（返回元组）"""
    response = {
        'code': code,
        'message': message,
        'timestamp': int(time.time() * 1000),
    }
    if errors is not None:
        response['errors'] = errors
    return response, status_code
