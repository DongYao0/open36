"""
Custom exceptions and exception handler
"""
from rest_framework.views import exception_handler
from django.utils import timezone


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        data = {
            'code': response.status_code,
            'message': response.data.get('detail', '请求处理失败'),
            'timestamp': int(timezone.now().timestamp() * 1000),
        }
        if 'detail' in response.data:
            del response.data['detail']
        if response.data:
            data['errors'] = response.data
        response.data = data
    return response


class ServiceError(Exception):
    pass
