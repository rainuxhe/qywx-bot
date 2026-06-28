from .base import BaseMixin


class DidaMixin(BaseMixin):
    @property
    def thirdparties_dida365_url(self) -> str:
        return self._get_conf(f"thirdparties", "dida365", "url", default="")

    @property
    def thirdparties_dida365_token(self) -> str:
        return self._get_conf(f"thirdparties", "dida365", "token", default="")

    @property
    def thirdparties_dida365_enabled(self) -> bool:
        return self._get_conf(f"thirdparties", "dida365", "enabled", default=False)


class BoChaMixin(BaseMixin):
    @property
    def thirdparties_bocha_enabled(self) -> bool:
        return self._get_conf(f"thirdparties", "bocha", "enabled", default=False)

    @property
    def thirdparties_bocha_url(self) -> str:
        return self._get_conf(f"thirdparties", "bocha", "url", default="")

    @property
    def thirdparties_bocha_token(self) -> str:
        return self._get_conf(f"thirdparties", "bocha", "token", default="")


class ThirdPartiesMixin(DidaMixin, BoChaMixin): ...
