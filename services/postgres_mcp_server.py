from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated
from db.connector import Database
from services.database_config import Config
from services.database_schema_service import DatabaseSchemaService
from services.sql_query_service import QueryService

class PostgresMcpServer:
    def __init__(self, config: Config):
        self.app = FastAPI(lifespan=self.lifespan)
        self.app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

        self.db = Database(config)
        self.schema_service = DatabaseSchemaService(self.db, config.schema_cache_ttl)
        self.query_service = QueryService(self.db)

        self.mcp = FastMCP(
            name="Postgres MCP Server",
            app=self.app,
            instructions="""
                This server provides data analysis tools.
                Use get_schema() to inspect tables.
                Use execute_query(sql) to run queries.
            """,
            transport="http",
            host=config.host,
            port=config.port,
            log_level=config.log_level,
            tools=[]
        )

        self.register_tools()

    def register_tools(self):
        @self.mcp.resource("schema://analysis")
        async def get_schema():
            return await self.schema_service.get_schema()

        @self.mcp.tool()
        async def execute_query(
            sql: Annotated[str, Field(description="SQL SELECT statement")],
        ):
            return await self.query_service.execute(sql)

    async def lifespan(self, app: FastAPI):
        yield
        await self.db.dispose()

    async def run(self):
        await self.mcp.run_streamable_http_async()