import asyncpg
from typing import AsyncGenerator
from fastapi.concurrency import asynccontextmanager
from services.database_config import Config

class Database:
    def __init__(self, config: Config):
        self.database_url = config.database_url
        self.schema = config.schema
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=self.database_url)

    async def dispose(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_conn(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if not self.pool:
            raise RuntimeError("Database connection pool is not initialized.")
        
        async with self.pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {self.schema}")
            yield conn
