from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent_graph import query_agentic
from src.models import ChatRequest, ChatResponse, HealthResponse
from src.rag import query

app = FastAPI(title="Witcher 3 Wiki Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    if body.mode == "agentic":
        result = query_agentic(body.question, body.history)
    else:
        result = query(body.question, body.history)
    return ChatResponse(**result)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        from src.llm import get_vectorstore

        vs = get_vectorstore()
        count = vs._collection.count()
        return HealthResponse(status="ok", pages_indexed=count)
    except Exception:
        return HealthResponse(status="degraded", pages_indexed=0)
