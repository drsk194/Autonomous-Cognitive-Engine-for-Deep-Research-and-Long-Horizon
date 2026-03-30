from fastapi import FastAPI
from pydantic import BaseModel

from eval import evaluate_output
from run import run_supervisor
from memory import search_memory, MEMORY_FILE
import json, os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestModel(BaseModel):
    query: str


@app.get("/")
def home():
    return {"message": "Supervisor Agent API Running"}


@app.get("/memory")
def get_memory():
    """Return all saved memory entries for the history sidebar."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Return topic + todos + truncated summary for each entry
        result = []
        for item in reversed(data):  # newest first
            result.append({
                "topic": item.get("topic", ""),
                "summary": item.get("summary", ""),
                "todos": item.get("todos", []),
                "delegation_log": item.get("delegation_log", []),
            })
        return result
    except Exception:
        return []


@app.post("/run")
def run_query(request: RequestModel):
    from memory import search_memory
    cached = search_memory(request.query)
    from_memory = bool(cached)
    report = run_supervisor(request.query)
    score = evaluate_output(report)
    return {"report": report, "score": score, "from_memory": from_memory}


