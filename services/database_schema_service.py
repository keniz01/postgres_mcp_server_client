from collections import defaultdict
import time
from sqlalchemy import text

class DatabaseSchemaService:
    def __init__(self, db: Database, ttl: int):
        self.db = db
        self.ttl = ttl
        self._cache = None
        self._cache_ts = 0

    async def fetch_schema(self) -> str:
        query = text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = :schema
            ORDER BY table_name, ordinal_position
        """)
        async with self.db.get_conn() as conn:
            result = await conn.execute(query, {"schema": self.db.schema})
            rows = result.fetchall()

        grouped = defaultdict(list)
        for table, column, dtype in rows:
            grouped[table].append(f"  {column}: {dtype}")
        return "\n".join(f"{table}:\n" + "\n".join(cols) for table, cols in grouped.items())

    async def get_schema(self) -> str:
        now = time.time()
        if not self._cache or (now - self._cache_ts) > self.ttl:
            self._cache = await self.fetch_schema()
            self._cache_ts = now
        return self._cache