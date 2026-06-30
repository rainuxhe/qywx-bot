from typing import Annotated
from urllib.parse import quote_plus

from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    host: Annotated[str, Field(..., description="PostgreSQL host")]
    port: Annotated[int, Field(..., description="PostgreSQL port")]
    user: Annotated[str, Field(..., description="PostgreSQL user")]
    password: Annotated[str, Field(..., description="PostgreSQL password")]
    dbname: Annotated[str, Field(..., description="PostgreSQL database name")]
    pool_min_size: Annotated[int, Field(..., description="Minimum size of PostgreSQL connection pool")]
    pool_max_size: Annotated[int, Field(..., description="Maximum size of PostgreSQL connection pool")]

    def get_dsn(self) -> str:
        """Get PostgreSQL connection string (DSN)"""
        user = quote_plus(self.user)
        password = quote_plus(self.password)
        return f"postgresql://{user}:{password}@{self.host}:{self.port}/{self.dbname}"


class DatabaseConfig(BaseModel):
    postgres: PostgresConfig
