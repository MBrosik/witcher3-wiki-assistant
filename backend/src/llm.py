from __future__ import annotations

import chromadb
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.config import settings
from src.embeddings import get_embeddings

LLM = ChatOpenAI | ChatAnthropic | ChatOllama


def get_llm() -> LLM:
    provider = settings.llm_provider

    match provider:
        case "deepseek":
            if not settings.deepseek_api_key:
                raise ValueError(
                    "LLM_PROVIDER=deepseek requires DEEPSEEK_API_KEY in the environment"
                )
            return ChatOpenAI(
                model=settings.deepseek_model,
                api_key=SecretStr(settings.deepseek_api_key),
                base_url="https://api.deepseek.com",
                temperature=0.0,
            )
        case "openai":
            return ChatOpenAI(
                model=settings.openai_model,
                temperature=0.0,
            )
        case "claude":
            return ChatAnthropic(
                model_name=settings.anthropic_model,
                temperature=0.0,
                timeout=None,
                stop=None,
            )
        case "ollama":
            return ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_llm_host,
                temperature=0.0,
            )
        case _:
            raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def get_vectorstore() -> Chroma:
    chroma_client = chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )
    return Chroma(
        client=chroma_client,
        collection_name="witcher_wiki",
        embedding_function=get_embeddings(),
    )
