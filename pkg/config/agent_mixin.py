from .base import BaseMixin

class AgentMixin(BaseMixin):
    @property
    def agent_base_url(self) -> str:
        return self._get_conf("agent", "base_url", default="")
    
    @property
    def agent_api_key(self) -> str:
        return self._get_conf("agent", "api_key", default="")
    
    @property
    def agent_model(self) -> str:
        return self._get_conf("agent", "model", default="")