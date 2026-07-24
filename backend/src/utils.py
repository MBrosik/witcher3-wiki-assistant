from __future__ import annotations

from typing import Any, NamedTuple

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate


class TokenUsage(NamedTuple):
    input_tokens: int
    output_tokens: int


class InvokeResult(NamedTuple):
    text: str
    tokens: TokenUsage


def format_context(docs: list[Document]) -> str:
    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        title = doc.metadata.get("page_title", "Unknown")
        parts.append(f"[{i}] {title}\n{doc.page_content}\n")
    return "\n---\n".join(parts)


def extract_sources(docs: list[Document]) -> list[dict[str, str]]:
    return [
        {
            "title": doc.metadata.get("page_title", "Unknown"),
            "url": doc.metadata.get("source_url", ""),
            "excerpt": doc.page_content[:300] + "...",
        }
        for doc in docs
    ]


def format_history(history: list[dict[str, str]] | None) -> str:
    if not history:
        return "(none)"
    lines: list[str] = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def clean_query(text: str) -> str:
    return text.strip().strip('"').strip("'")


def message_text(message: Any) -> str:
    """Extract a plain string from a LangChain message object."""
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content)


def extract_token_usage(message: Any) -> TokenUsage:
    """
    Read input/output tokens from a LangChain AIMessage.

    Supports ``usage_metadata`` (LC standard) and OpenAI-style
    ``response_metadata``.
    """
    usage = getattr(message, "usage_metadata", None) or {}
    if usage:
        return TokenUsage(
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
        )

    meta = getattr(message, "response_metadata", None) or {}
    token_usage = meta.get("token_usage") or meta.get("usage") or {}
    return TokenUsage(
        input_tokens=int(
            token_usage.get("prompt_tokens") or token_usage.get("input_tokens") or 0
        ),
        output_tokens=int(
            token_usage.get("completion_tokens")
            or token_usage.get("output_tokens")
            or 0
        ),
    )


def invoke_text(
    llm: Any,
    prompt: ChatPromptTemplate,
    variables: dict[str, Any],
) -> InvokeResult:
    """Invoke ``prompt | llm`` (no StrOutputParser) and return text + token usage."""
    message = (prompt | llm).invoke(variables)
    usage = extract_token_usage(message)
    return InvokeResult(text=message_text(message), tokens=usage)
