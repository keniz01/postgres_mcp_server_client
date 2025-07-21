from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db.validator import is_safe_query
from db.connector import Database

router = APIRouter()

class QueryRequest(BaseModel):
    sql: str

# Dependency placeholder, to be overridden on app start
async def get_db() -> Database:
    raise RuntimeError("Database dependency not set")

@router.post("/query")
async def execute_query(request: QueryRequest, database: Database = Depends(get_db)):
    if not is_safe_query(request.sql):
        raise HTTPException(status_code=400, detail="Only SELECT statements are allowed.")
    try:
        results = await database.fetch(request.sql)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
