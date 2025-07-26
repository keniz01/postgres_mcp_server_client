from fastapi import APIRouter, FastAPI, HTTPException
from fastmcp import Client
from src.llama_model_manager import LlamaModelManager
from src.operation_timer import CallTimer
from typing import List, Dict
from models.query_models import QueryRequest, QueryResponse

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SQL Generator API",
    description="This API takes a natural language question and returns a Postgres SQL query based on the database schema context.",
    version="1.0.0"
)

# --- APIRouter Initialization ---
router = APIRouter(prefix="/query", tags=["Query"])

# --- Helper Function to Build Prompt ---
def create_messages(question: str, context: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You must use the context to generate a correct Postgres SQL statement to answer the question at the end.\n"
                "Strictly only use table and column names defined in the context and you must use table and column aliases.\n"
                "If the question does not make sense or you don't know the answer just say \"I don't know\".\n"
                "You must only return valid SQL - do not explain, advise or assume."
            )
        },
        {"role": "user", "content": "Count albums distributed by record label 'Greenesleeves'"},
        {"role": "assistant", "content": (
            "select count(a.*) album_count \n"
            "from album a \n"
            "inner join record_label rl on rl.label_id = a.label_id \n"
            "where rl.label_name ILIKE 'Greensleeves Records';"
        )},
        {"role": "user", "content": "How many albums does the recording artist 'Gregory Isaacs' have?"},
        {"role": "assistant", "content": (
            "SELECT COUNT(al.*) \n"
            "FROM album al;"
        )},
        {"role": "user", "content": "Show all tracks on the album 'Soca Xplosion 2007' have?"},
        {"role": "assistant", "content": (
            "SELECT tr.track_id, tr.title, tr.duration, tr.position, tr.release_year, tr.genre_id, tr.label_id, tr.artist_id, tr.album_id \n"
            "FROM track tr\n"
            "INNER JOIN album al on al.album_id = tr.album_id \n"
            "WHERE al.title ILIKE 'Soca Xplosion';"
        )},
        {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
    ]


# --- Endpoint Logic ---
@CallTimer
@router.post(
    "",
    response_model=QueryResponse,
    summary="Generate SQL from a natural language question",
    description="""
This endpoint takes a natural language question, uses a preloaded schema context, and returns:
- A valid SQL query based on that schema
- The query execution result

It uses a language model to convert the prompt and few-shot examples into SQL.
"""
)
async def generate_sql_query(request: QueryRequest) -> QueryResponse:
    try:
        async with Client("http://localhost:8080/mcp") as client:
            schema_resource = await client.read_resource("schema://analysis")
            schema = schema_resource[0].text

            llama_model = LlamaModelManager.get_instance()
            response = llama_model.create_chat_completion(
                messages=create_messages(request.question, schema),
                temperature=0.2,
                top_p=0.8,
                max_tokens=1024
            )

            sql = response["choices"][0]["message"]["content"].strip()
            result = await client.call_tool("execute_query", {"sql": sql})

            return QueryResponse(sql=sql, result=result.content)

    except Exception as e:
        # Optional: log traceback here
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# --- Register Router ---
app.include_router(router)
