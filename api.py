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
                "label": item.get("label", item.get("topic", "")),  # label for sidebar, topic for chat
                "summary": item.get("summary", ""),
                "todos": item.get("todos", []),
                "delegation_log": item.get("delegation_log", []),
                "starred": item.get("starred", False),
            })
        return result
    except Exception:
        return []




@app.delete("/memory/{index}")
def delete_memory(index: int):
    """Delete a memory entry by index."""
    if not os.path.exists(MEMORY_FILE):
        return {"ok": False}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # /memory returns newest-first, so reverse index
        real_idx = len(data) - 1 - index
        if 0 <= real_idx < len(data):
            data.pop(real_idx)
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return {"ok": True}
        return {"ok": False, "error": "Index out of range"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class RenameModel(BaseModel):
    index: int
    topic: str

@app.post("/memory/rename")
def rename_memory(req: RenameModel):
    """Rename display label of a memory entry. Stores in 'label', keeps original 'topic'."""
    if not os.path.exists(MEMORY_FILE):
        return {"ok": False}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        real_idx = len(data) - 1 - req.index
        if 0 <= real_idx < len(data):
            data[real_idx]["label"] = req.topic   # store as label, don't touch topic
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return {"ok": True}
        return {"ok": False, "error": "Index out of range"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class StarModel(BaseModel):
    index: int
    starred: bool

@app.post("/memory/star")
def star_memory(req: StarModel):
    """Toggle star on a memory entry."""
    if not os.path.exists(MEMORY_FILE):
        return {"ok": False}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        real_idx = len(data) - 1 - req.index
        if 0 <= real_idx < len(data):
            data[real_idx]["starred"] = req.starred
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return {"ok": True}
        return {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}
@app.post("/run")
def run_query(request: RequestModel):
    from memory import search_memory
    cached = search_memory(request.query)
    from_memory = bool(cached)
    report, is_simple, judge_scores = run_supervisor(request.query)
    score = "—" if is_simple else evaluate_output(report)
    return {
        "report": report,
        "score": score,
        "from_memory": from_memory,
        "is_simple": is_simple,
        "judge_scores": judge_scores,
    }


