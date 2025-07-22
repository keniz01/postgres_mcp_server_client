import asyncio
import time
import json
from contextlib import asynccontextmanager
from collections import defaultdict
from configparser import ConfigParser

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from sqlalchemy import text
from mcp.server.fastmcp import FastMCP
from typing import Annotated, AsyncGenerator
from pydantic import Field

# ────────────────────────────────────────────────────────────────────────────────
# LOAD CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────────

config = ConfigParser()
config.read("config.ini")

DATABASE_URL = config["database"]["url"]
DB_SCHEMA = config["database"].get("schema", "public")
SCHEMA_CACHE_TTL = int(config["cache"].get("schema_ttl", 300))
SCHEMA_LIMIT = config["rate_limit"].get("schema_limit", "5/minute")
QUERY_LIMIT = config["rate_limit"].get("query_limit", "10/minute")
HOST = config["server"].get("host", "127.0.0.1")
PORT = int(config["server"].get("port", 8080))
LOG_LEVEL = config["server"].get("log_level", "INFO")

# ────────────────────────────────────────────────────────────────────────────────
# DATABASE SETUP
# ────────────────────────────────────────────────────────────────────────────────

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

@asynccontextmanager
async def get_conn() -> AsyncGenerator[AsyncConnection, None]:
    async with engine.connect() as conn:
        await conn.execute(text(f"SET search_path TO {DB_SCHEMA}"))
        yield conn

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

# ────────────────────────────────────────────────────────────────────────────────
# INIT FASTAPI
# ────────────────────────────────────────────────────────────────────────────────

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ────────────────────────────────────────────────────────────────────────────────
# INIT FASTMCP
# ────────────────────────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="Postgres MCP Server",
    app=app,
    instructions="""
        This server provides data analysis tools.
        Use get_schema() to inspect tables.
        Use execute_query(sql) to run queries.
    """,
    transport="http", 
    host=HOST, 
    port=PORT, 
    log_level=LOG_LEVEL,
    tools=[]
)

_schema_cache = None
_schema_cache_ts = 0

async def fetch_schema() -> str:
    query = text("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = :schema
        ORDER BY table_name, ordinal_position
    """)
    async with get_conn() as conn:
        result = await conn.execute(query, {"schema": DB_SCHEMA})
        rows = result.fetchall()

    grouped = defaultdict(list)
    for table, column, dtype in rows:
        grouped[table].append(f"  {column}: {dtype}")
    return "\n".join(f"{table}:\n" + "\n".join(cols) for table, cols in grouped.items())

@mcp.resource("schema://analysis")
async def get_schema() -> str:
    global _schema_cache, _schema_cache_ts
    now = time.time()
    if not _schema_cache or (now - _schema_cache_ts) > SCHEMA_CACHE_TTL:
        _schema_cache = await fetch_schema()
        _schema_cache_ts = now
    return _schema_cache

@mcp.tool()
async def execute_query(
    sql: Annotated[ str, Field( description="SQL SELECT statement")],
):
    # start_time = time.time()
    try:
        if not sql.lower().startswith(("select", "insert", "update", "delete")):
            return "Only SELECT, INSERT, UPDATE, DELETE statements are allowed."

        async with get_conn() as conn:
            cursor_result = await conn.execute(text(sql))
            if cursor_result.returns_rows:
                sql_response_context = cursor_result.fetchall() 
                return sql_response_context
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

async def main():
    await mcp.run_streamable_http_async()

if __name__ == "__main__":
    asyncio.run(main())
