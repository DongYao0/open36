"""
Consul client for service registration and discovery
"""
import logging
import consul
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ConsulClient:
    def __init__(self):
        self.consul_url = settings.CONSUL_URL
        self.service_name = settings.CONSUL_SERVICE_NAME
        self.service_id = settings.CONSUL_SERVICE_ID
        self.service_port = settings.SERVICE_PORT
        self.service_host = settings.SERVICE_HOST

        try:
            host = self.consul_url.replace('http://', '').replace('https://', '')
            self.c = consul.Consul(host=host.split(':')[0], port=8500)
            logger.info(f"Consul client initialized: {self.consul_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Consul client: {e}")
            self.c = None

    def register(self):
        if not self.c:
            logger.warning("Consul not available, skipping registration")
            return False
        try:
            self.c.agent.service.register(
                name=self.service_name,
                service_id=self.service_id,
                address=self.service_host,
                port=self.service_port,
                check=consul.Check.http(
                    url=f"http://{self.service_host}:{self.service_port}/health/",
                    interval="30s",
                    timeout="5s"
                ),
                tags=["forum-service", "django", "api"]
            )
            logger.info(f"Service registered: {self.service_name} ({self.service_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            return False

    def deregister(self):
        if not self.c:
            return False
        try:
            self.c.agent.service.deregister(self.service_id)
            logger.info(f"Service deregistered: {self.service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")
            return False

    def discover_service(self, service_name, cache_ttl=300):
        cache_key = f"consul:service:{service_name}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        if not self.c:
            return None
        try:
            _, services = self.c.health.service(service_name, passing=True)
            if services:
                service = services[0]['Service']
                address = f"http://{service['Address']}:{service['Port']}"
                cache.set(cache_key, address, cache_ttl)
                return address
        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {e}")
        return None


consul_client = ConsulClient()
