import asyncpg
import logging
from typing import Optional
from config import load_db_config

logger = logging.getLogger(__name__)

class Database:
    """
    A PostgreSQL async database wrapper that manages schema scoping using asyncpg.
    Ensures `search_path` is set for each acquired connection.
    """
    __db_config = load_db_config()

    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        self._quoted_schema = self._quote_ident(schema_name)
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """
        Initialize the connection pool and set up the search path for new connections.
        """
        async def _setup_connection(conn: asyncpg.Connection):
            await conn.execute(f"SET search_path TO {self._quoted_schema}")
            val = await conn.fetchval("SHOW search_path")
            logger.debug(f"New connection setup with search_path: {val}")

        logger.info("Connecting to the database...")
        self._pool = await asyncpg.create_pool(
            **self.__db_config,
            init=_setup_connection
        )
        logger.info("Database pool created successfully.")

    async def disconnect(self) -> None:
        """
        Closes the database connection pool.
        """
        if self._pool:
            await self._pool.close()
            logger.info("Database pool disconnected.")

    async def fetch(self, query: str, *args) -> list[dict]:
        """
        Executes a SELECT query and returns results as a list of dictionaries.
        Ensures `search_path` is set per connection acquired from the pool.
        """
        if not self._pool:
            raise RuntimeError("Database connection pool is not initialized.")

        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction(readonly=True):
                    await conn.execute(f'SET search_path TO {self._quoted_schema}')
                    rows = await conn.fetch(query, *args)
                    logger.debug(f"Executed query: {query}")
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.exception(f"Error executing query: {query}")
            raise

    def _quote_ident(self, ident: str) -> str:
        """
        Properly quotes an SQL identifier to prevent injection.
        """
        return '"' + ident.replace('"', '""') + '"'
