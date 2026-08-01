"""
Unified response utilities
"""
from django.utils import timezone


def success_response(data=None, message='success', code=200):
    response = {
        'code': code,
        'message': message,
        'timestamp': int(timezone.now().timestamp() * 1000),
    }
    if data is not None:
        response['data'] = data
    return response


def error_response(message, code=400, errors=None, status_code=400):
    response = {
        'code': code,
        'message': message,
        'timestamp': int(timezone.now().timestamp() * 1000),
    }
    if errors is not None:
        response['errors'] = errors
    return response, status_code
