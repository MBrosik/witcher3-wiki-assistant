from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

RagMode = Literal["adaptive", "agentic"]


class ChatRequest(BaseModel):
    question: str
    history: list[dict[str, str]] | None = None
    mode: RagMode = "adaptive"


class Source(BaseModel):
    title: str
    url: str
    excerpt: str


class Tokens(BaseModel):
    input: int
    output: int


class AgentStep(BaseModel):
    type: str
    query: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    tokens: Tokens
    response_time_ms: int
    mode: RagMode = "adaptive"
    agent_steps: list[AgentStep] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    pages_indexed: int


class AgentStepDict(TypedDict, total=False):
    type: str
    query: str


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    docs: list[Document]
    steps: list[AgentStepDict]
    input_tokens: int
    output_tokens: int
    tool_rounds: int
