from .base import BaseMixin

class ServiceMixin(BaseMixin):
    @property
    def service_host(self) -> str:
        return self._get_conf("service", "host", default="127.0.0.1")
    
    @property
    def service_port(self) -> int:
        return self._get_conf("service", "port", default=8000)
    
    @property
    def service_log_level(self) -> str:
        return self._get_conf("service", "log", "level", default="info")