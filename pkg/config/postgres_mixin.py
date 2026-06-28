from urllib.parse import quote_plus

from .base import BaseMixin


class PostgresMixin(BaseMixin):
    @property
    def postgres_host(self) -> str:
        return self._get_conf("database", "postgres", "host", default="127.0.0.1")

    @property
    def postgres_port(self) -> int:
        return self._get_conf("database", "postgres", "port", default=5432)

    @property
    def postgres_user(self) -> str:
        return self._get_conf("database", "postgres", "user", default="")

    @property
    def postgres_password(self) -> str:
        return self._get_conf("database", "postgres", "password", default="")

    @property
    def postgres_dbname(self) -> str:
        return self._get_conf("database", "postgres", "dbname", default="")

    @property
    def postgres_pool_size_min(self) -> int:
        return self._get_conf("database", "postgres", "pool_min_size", default=2)

    @property
    def postgres_pool_size_max(self) -> int:
        return self._get_conf("database", "postgres", "pool_max_size", default=10)

    def get_postgres_dsn(self) -> str:
        """Get PostgreSQL connection string (DSN)"""
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return f"postgresql://{user}:{password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_dbname}"
