"""
Content app tests: /api/resources/（复用 Post 模型 + section='share'）
"""
import os
import django
from django.conf import settings

# 测试环境必须在 import models 前设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')
if not settings.configured:
    django.setup()
