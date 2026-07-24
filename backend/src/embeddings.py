from __future__ import annotations

import os
from typing import cast

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from src.config import settings


class VoyageEmbeddings(Embeddings):
    def __init__(self, model: str = "voyage-4-lite") -> None:
        import voyageai

        self.model = model
        self._client = voyageai.Client()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        result = self._client.embed(
            texts,
            model=self.model,
            input_type="document",
        )
        return cast("list[list[float]]", list(result.embeddings))

    def embed_query(self, text: str) -> list[float]:
        result = self._client.embed(
            [text],
            model=self.model,
            input_type="query",
        )
        return cast("list[float]", list(result.embeddings[0]))


def get_embeddings() -> Embeddings:
    provider = settings.embedding_provider

    match provider:
        case "voyage":
            if not os.getenv("VOYAGE_API_KEY"):
                raise ValueError(
                    "EMBEDDING_PROVIDER=voyage requires VOYAGE_API_KEY in the environment"
                )
            return VoyageEmbeddings(model=settings.voyage_model)
        case "ollama":
            return OllamaEmbeddings(
                model=settings.ollama_embed_model,
                base_url=settings.ollama_host,
            )
        case _:
            raise ValueError(
                f"Unknown EMBEDDING_PROVIDER: {provider!r} "
                "(expected 'voyage' or 'ollama')"
            )


def embedding_provider_label() -> str:
    provider = settings.embedding_provider
    if provider == "voyage":
        return f"voyage/{settings.voyage_model}"
    if provider == "ollama":
        return f"ollama/{settings.ollama_embed_model}"
    return provider
