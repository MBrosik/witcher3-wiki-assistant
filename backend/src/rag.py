from __future__ import annotations

import time
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import settings
from src.llm import LLM, get_llm, get_vectorstore
from src.prompts import PROMPT, REWRITE_PROMPT, SEARCH_REWRITE_PROMPT
from src.utils import (
    TokenUsage,
    clean_query,
    extract_sources,
    format_context,
    format_history,
    invoke_text,
)


def rewrite_standalone(
    llm: LLM,
    question: str,
    history: list[dict[str, str]] | None,
) -> tuple[str, TokenUsage]:
    result = invoke_text(
        llm,
        REWRITE_PROMPT,
        {"history": format_history(history), "question": question},
    )
    return clean_query(result.text), result.tokens


def rewrite_for_search(llm: LLM, query: str) -> tuple[str, TokenUsage]:
    result = invoke_text(llm, SEARCH_REWRITE_PROMPT, {"query": query})
    return clean_query(result.text), result.tokens


def retrieve_with_scores(
    vectorstore: Chroma,
    search_query: str,
    k: int = settings.retrieval_k,
) -> tuple[list[Document], float]:
    results = vectorstore.similarity_search_with_score(search_query, k=k)
    if not results:
        return [], float("inf")
    docs = [doc for doc, _score in results]
    best_distance = min(score for _doc, score in results)
    return docs, best_distance


def retrieve_docs(
    llm: LLM,
    vectorstore: Chroma,
    question: str,
    history: list[dict[str, str]] | None,
) -> tuple[list[Document], TokenUsage]:
    total_tokens = TokenUsage(input_tokens=0, output_tokens=0)

    standalone, tokens = rewrite_standalone(llm, question, history)
    total_tokens = TokenUsage(
        input_tokens=total_tokens.input_tokens + tokens.input_tokens,
        output_tokens=total_tokens.output_tokens + tokens.output_tokens,
    )

    docs, best = retrieve_with_scores(vectorstore, standalone)

    if best <= settings.retrieval_distance_threshold:
        return docs, total_tokens

    standalone2, tokens2 = rewrite_for_search(llm, standalone)
    total_tokens = TokenUsage(
        input_tokens=total_tokens.input_tokens + tokens2.input_tokens,
        output_tokens=total_tokens.output_tokens + tokens2.output_tokens,
    )

    docs2, best2 = retrieve_with_scores(vectorstore, standalone2)
    return (docs2 if best2 < best else docs), total_tokens


def query(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    start = time.time()

    llm = get_llm()
    vectorstore = get_vectorstore()
    docs, usage = retrieve_docs(llm, vectorstore, question, history)

    # Generate from the original question so the answer language matches the user.
    result = invoke_text(
        llm,
        PROMPT,
        {"context": format_context(docs), "question": question},
    )
    total_tokens = TokenUsage(
        input_tokens=usage.input_tokens + result.tokens.input_tokens,
        output_tokens=usage.output_tokens + result.tokens.output_tokens,
    )

    elapsed_ms = int((time.time() - start) * 1000)

    return {
        "answer": result.text,
        "sources": extract_sources(docs),
        "tokens": {
            "input": total_tokens.input_tokens,
            "output": total_tokens.output_tokens,
        },
        "response_time_ms": elapsed_ms,
        "mode": "adaptive",
        "agent_steps": [],
    }
