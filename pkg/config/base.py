from typing import Dict, Any

class BaseMixin:
    _config: Dict[str, Any] = {}

    def _get_conf(self, *keys: str, default: Any = None) -> Any:
        """递归获取配置"""
        data = self._config
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k)
            else:
                return default
        return data if data is not None else default