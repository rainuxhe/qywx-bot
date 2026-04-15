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

    def get_postgres_dsn(self) -> str:
        """Get PostgreSQL connection string (DSN)"""
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_dbname}"
        )
