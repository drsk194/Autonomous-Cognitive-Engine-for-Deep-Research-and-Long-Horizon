from fastapi import FastAPI
from pydantic import BaseModel

from eval import evaluate_output
from run import run_supervisor

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ ADD CORS HERE (after app = FastAPI())
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
    return {
        "message": "Supervisor Agent API Running"
    }


@app.post("/run")
def run_query(request: RequestModel):

    report = run_supervisor(request.query)

    score = evaluate_output(report)

    return {
        "report": report,
        "score": score
    }


