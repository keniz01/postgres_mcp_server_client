import asyncio
from services.database_config import Config
from services.postgres_mcp_server import PostgresMcpServer

async def main():
    config = Config()
    app = PostgresMcpServer(config)
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
