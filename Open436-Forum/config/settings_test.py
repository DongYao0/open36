"""
Test settings for Forum Service —— 使用 SQLite 内存数据库，跑快速 API 测试。
"""
from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 关闭 Consul / 内部 HTTP 调用
CONSUL_URL = ''
AUTH_SERVICE_URL = ''
FILE_SERVICE_URL = ''
INTERNAL_API_KEY = 'test-internal-key'

# 关闭签到数据迁移（Forum content app 是表由 SQL 直建，非 Django 模型层）
# 在测试 setUp 中手工建表

SECRET_KEY = 'test-secret'
DEBUG = False
ALLOWED_HOSTS = ['*']