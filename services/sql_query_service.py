
from sqlalchemy import text

from db.connector import Database


class QueryService:
    def __init__(self, db: Database):
        self.db = db

    async def execute(self, sql: str):
        if not sql.lower().startswith(("select", "insert", "update", "delete")):
            return "Only SELECT, INSERT, UPDATE, DELETE statements are allowed."

        try:
            async with self.db.get_conn() as conn:
                result = await conn.execute(text(sql))
                if result.returns_rows:
                    return result.fetchall()
                return "Query executed successfully."
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"