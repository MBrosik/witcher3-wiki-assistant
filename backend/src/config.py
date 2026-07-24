from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    llm_provider: str = field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "deepseek"),
    )
    deepseek_api_key: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""),
    )
    deepseek_model: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"),
    )
    anthropic_model: str = field(
        default_factory=lambda: os.getenv(
            "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"
        ),
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
    )
    ollama_llm_host: str = field(
        default_factory=lambda: os.getenv(
            "OLLAMA_LLM_HOST",
            os.getenv("OLLAMA_HOST", "http://ollama-llm:11434"),
        ),
    )

    embedding_provider: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "voyage"),
    )
    voyage_api_key: str = field(
        default_factory=lambda: os.getenv("VOYAGE_API_KEY", ""),
    )
    voyage_model: str = field(
        default_factory=lambda: os.getenv("VOYAGE_MODEL", "voyage-4-lite"),
    )
    ollama_embed_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    )
    ollama_host: str = field(
        default_factory=lambda: os.getenv("OLLAMA_HOST", "http://ollama:11434"),
    )

    chroma_host: str = field(
        default_factory=lambda: os.getenv("CHROMA_HOST", "chromadb"),
    )
    chroma_port: int = field(
        default_factory=lambda: int(os.getenv("CHROMA_PORT", "8000")),
    )

    retrieval_k: int = 6
    retrieval_distance_threshold: float = field(
        default_factory=lambda: float(
            os.getenv("RETRIEVAL_DISTANCE_THRESHOLD", "1.0"),
        ),
    )

    agent_max_steps: int = field(
        default_factory=lambda: max(1, int(os.getenv("AGENT_MAX_STEPS", "3"))),
    )

    ingest_workers: int = field(
        default_factory=lambda: max(1, int(os.getenv("INGEST_WORKERS", "12"))),
    )
    ingest_embed_batch: int = field(
        default_factory=lambda: max(1, int(os.getenv("INGEST_EMBED_BATCH", "128"))),
    )


settings = Settings()
