"""
File Service (M7) client
"""
import requests
import logging
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from .consul_client import consul_client

logger = logging.getLogger(__name__)


class FileServiceClient:
    """
    文件服务客户端

    通过 Consul 发现 M7 文件服务并调用其 API
    """

    def __init__(self):
        self.service_name = getattr(settings, 'FILE_SERVICE_NAME', 'file-service')
        self.timeout = 5

    def _get_service_url(self) -> Optional[str]:
        cache_key = f'service_url:{self.service_name}'
        cached_url = cache.get(cache_key)
        if cached_url:
            return cached_url

        service_info = consul_client.discover_service(self.service_name)
        if not service_info:
            logger.warning(f"Cannot discover {self.service_name}")
            return None

        # consul_client.discover_service 返回 URL 字符串
        base_url = service_info if isinstance(service_info, str) else f"http://{service_info['host']}:{service_info['port']}"
        cache.set(cache_key, base_url, 300)
        return base_url

    def get_file_url(self, file_id: str) -> Optional[str]:
        if not file_id:
            return None

        cache_key = f'file_url:{file_id}'
        cached_url = cache.get(cache_key)
        if cached_url:
            return cached_url

        base_url = self._get_service_url()
        if not base_url:
            logger.error("File service not available")
            return None

        try:
            response = requests.get(f"{base_url}/files/{file_id}", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'url' in data['data']:
                    url = data['data']['url']
                    cache.set(cache_key, url, 600)
                    return url
            else:
                logger.warning(f"Failed to get file URL for {file_id}: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout when requesting file {file_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting file {file_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting file URL: {e}")
        return None


file_service_client = FileServiceClient()
