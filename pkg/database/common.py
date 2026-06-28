from urllib.parse import quote_plus

from psycopg_pool import AsyncConnectionPool

from pkg.config import cfg


_PG_POOL: AsyncConnectionPool = None  # type: ignore


def _init_pg_pool():
    global _PG_POOL
    if not _PG_POOL:
        _PG_POOL = AsyncConnectionPool(
            f"postgresql://{quote_plus(cfg.postgres_user)}:{quote_plus(cfg.postgres_password)}@{cfg.postgres_host}:{cfg.postgres_port}/{cfg.postgres_dbname}",
            min_size=cfg.postgres_pool_size_min,
            max_size=cfg.postgres_pool_size_max,
            open=False,  # 手动open, 避免阻塞
        )


async def get_pg_pool() -> AsyncConnectionPool:
    global _PG_POOL
    if not _PG_POOL:
        _init_pg_pool()
    await _PG_POOL.open()
    return _PG_POOL
