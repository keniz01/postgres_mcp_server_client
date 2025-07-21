from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routers import router, get_db as router_get_db
from db.connector import Database
import logging

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG if needed
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

db = Database(schema_name="music")

async def get_db():
    return db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(lifespan=lifespan)
app.dependency_overrides[router_get_db] = get_db
app.include_router(router, prefix="/api", tags=["Music API"])
