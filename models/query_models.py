# --- Request & Response Models ---
from typing import Any
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    result: Any