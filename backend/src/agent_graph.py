from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.config import settings
from src.llm import LLM, get_llm, get_vectorstore
from src.models import AgentState, AgentStepDict
from src.prompts import AGENT_SYSTEM, PROMPT
from src.rag import rewrite_for_search
from src.utils import (
    TokenUsage,
    extract_sources,
    extract_token_usage,
    format_context,
    format_history,
    invoke_text,
)


@dataclass
class ResearchContext:
    docs: list[Document] = field(default_factory=list)
    steps: list[AgentStepDict] = field(default_factory=list)
    token_usage: TokenUsage = field(default_factory=lambda: TokenUsage(0, 0))


def _doc_key(doc: Document) -> tuple[str, str]:
    return (
        str(doc.metadata.get("page_title", "")),
        doc.page_content[:120],
    )


def _merge_docs(
    existing: list[Document],
    new_docs: list[Document],
) -> list[Document]:
    seen = {_doc_key(d) for d in existing}
    merged = list(existing)
    for doc in new_docs:
        key = _doc_key(doc)
        if key not in seen:
            seen.add(key)
            merged.append(doc)
    return merged


def _format_search_results(
    results: list[tuple[Document, float]],
) -> str:
    if not results:
        return "No wiki chunks found for this query."
    parts: list[str] = []
    for i, (doc, score) in enumerate(results, 1):
        title = doc.metadata.get("page_title", "Unknown")
        excerpt = doc.page_content[:500]
        parts.append(f"[{i}] {title} (distance={score:.3f})\n{excerpt}")
    return "\n\n---\n\n".join(parts)


def _build_tools(
    vectorstore: Any,
    llm: LLM,
    ctx: ResearchContext,
) -> list[BaseTool]:

    @tool
    def search_wiki(query: str) -> str:
        results = vectorstore.similarity_search_with_score(
            query,
            k=settings.retrieval_k,
        )
        docs = [doc for doc, _score in results]
        ctx.docs = _merge_docs(ctx.docs, docs)
        ctx.steps.append({"type": "search", "query": query})
        return _format_search_results(results)

    @tool
    def refine_query(previous_query: str) -> str:
        refined, tokens = rewrite_for_search(llm, previous_query)
        ctx.token_usage = TokenUsage(
            input_tokens=ctx.token_usage.input_tokens + tokens.input_tokens,
            output_tokens=ctx.token_usage.output_tokens + tokens.output_tokens,
        )
        ctx.steps.append({"type": "refine", "query": refined})
        return (
            f"Refined search query: {refined}\nCall search_wiki with this query next."
        )

    return [search_wiki, refine_query]


def _route_after_agent(state: AgentState) -> Literal["tools", "generate"]:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "generate"


def _route_after_tools(state: AgentState) -> Literal["agent", "generate"]:
    if state["tool_rounds"] >= settings.agent_max_steps:
        return "generate"
    return "agent"


def build_agent_graph(
    llm: LLM,
    tools: list[BaseTool],
    ctx: ResearchContext,
) -> Any:
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def agent_node(state: AgentState) -> dict[str, Any]:
        response = llm_with_tools.invoke(state["messages"])
        usage = extract_token_usage(response)
        return {
            "messages": [response],
            "input_tokens": state["input_tokens"] + usage.input_tokens,
            "output_tokens": state["output_tokens"] + usage.output_tokens,
        }

    def tools_node(state: AgentState) -> dict[str, Any]:
        result = tool_node.invoke(state)
        delta = ctx.token_usage
        ctx.token_usage = TokenUsage(0, 0)
        return {
            "messages": result["messages"],
            "docs": list(ctx.docs),
            "steps": list(ctx.steps),
            "tool_rounds": state["tool_rounds"] + 1,
            "input_tokens": state["input_tokens"] + delta.input_tokens,
            "output_tokens": state["output_tokens"] + delta.output_tokens,
        }

    def generate_node(state: AgentState) -> dict[str, Any]:
        docs = state["docs"]
        result = invoke_text(
            llm,
            PROMPT,
            {"context": format_context(docs), "question": state["question"]},
        )
        steps = list(state["steps"])
        steps.append({"type": "generate"})
        return {
            "messages": [AIMessage(content=result.text)],
            "docs": docs,
            "steps": steps,
            "input_tokens": state["input_tokens"] + result.tokens.input_tokens,
            "output_tokens": state["output_tokens"] + result.tokens.output_tokens,
        }

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_node("generate", generate_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        _route_after_agent,
        {"tools": "tools", "generate": "generate"},
    )
    graph.add_conditional_edges(
        "tools",
        _route_after_tools,
        {"agent": "agent", "generate": "generate"},
    )
    graph.add_edge("generate", END)
    return graph.compile()


def query_agentic(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    start = time.time()
    llm = get_llm()
    vectorstore = get_vectorstore()
    ctx = ResearchContext()

    tools = _build_tools(vectorstore=vectorstore, llm=llm, ctx=ctx)
    app = build_agent_graph(llm, tools, ctx)

    user_blob = (
        f"Chat history:\n{format_history(history)}\n\n"
        f"User question: {question}\n\n"
        "Research this with tools, then stop when ready."
    )
    initial: AgentState = {
        "messages": [
            SystemMessage(content=AGENT_SYSTEM),
            HumanMessage(content=user_blob),
        ],
        "question": question,
        "docs": [],
        "steps": [],
        "input_tokens": 0,
        "output_tokens": 0,
        "tool_rounds": 0,
    }

    final = app.invoke(initial)
    docs: list[Document] = final["docs"]
    steps: list[AgentStepDict] = final["steps"]

    answer = final["messages"][-1].content

    elapsed_ms = int((time.time() - start) * 1000)
    return {
        "answer": answer,
        "sources": extract_sources(docs),
        "tokens": {
            "input": int(final.get("input_tokens") or 0),
            "output": int(final.get("output_tokens") or 0),
        },
        "response_time_ms": elapsed_ms,
        "mode": "agentic",
        "agent_steps": steps,
    }
