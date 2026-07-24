"""
Ingest script - fetches Witcher 3 wiki pages, chunks them, embeds them,
and loads the vectors into ChromaDB.

Usage::

    docker compose run --rm backend python -m src.ingest

Env:
    INGEST_WORKERS=12        - parallel fetch workers (default 12).
    INGEST_EMBED_BATCH=128   - chunks per embed API request (default 128).
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TypedDict

import chromadb
import mwclient
import mwparserfromhell
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings
from src.embeddings import embedding_provider_label, get_embeddings

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


WIKI_URL = "witcher.fandom.com"
WIKI_PATH = "/"
CATEGORIES: list[str] = [
    # Core gameplay lore
    "The Witcher 3 characters",
    "The Witcher 3 bestiary",
    "The Witcher 3 locations",
    # Quests
    "The Witcher 3 main quests",
    "The Witcher 3 secondary quests",
    "The Witcher 3 contracts",
    "The Witcher 3 treasure hunts",
    # Gear / crafting (Grandmaster sets, diagrams, materials)
    "The Witcher 3 witcher gear",
    "The Witcher 3 armor",
    "The Witcher 3 weapons",
    "The Witcher 3 crafting diagrams",
    "The Witcher 3 crafting components",
    # Alchemy
    "The Witcher 3 alchemy",
    "The Witcher 3 alchemy formulae",
    "The Witcher 3 potions",
    # Blood and Wine
    "Blood and Wine characters",
    "Blood and Wine bestiary",
    "Blood and Wine locations",
    "Blood and Wine quests",
    "Blood and Wine witcher gear",
    "Blood and Wine crafting diagrams",
    "Blood and Wine crafting components",
    "Blood and Wine alchemy",
]
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_NAME = "witcher_wiki"
RAW_DATA_DIR = Path("/app/data/raw")

# MediaWiki namespace for Category: pages (skip subcategory stubs when listing)
NS_CATEGORY = 14

_thread_local = threading.local()
_print_lock = threading.Lock()


def connect_to_wiki(*, quiet: bool = False) -> mwclient.Site:
    """Connect to the Witcher Fandom wiki."""
    site = mwclient.Site(WIKI_URL, path=WIKI_PATH)
    if not quiet:
        logger.info("Connected to %s", site.host)
    return site


def _thread_site() -> mwclient.Site:
    site = getattr(_thread_local, "site", None)
    if site is None:
        site = connect_to_wiki(quiet=True)
        _thread_local.site = site
    return site


def get_category_pages(
    site: mwclient.Site,
    categories: list[str],
) -> list[dict[str, str | int]]:
    """
    Collect unique article pages from the given categories (direct members only).

    Subcategory pages are skipped; list specific leaf categories instead.
    """
    pages: list[dict[str, str | int]] = []
    seen: set[str] = set()

    for category in categories:
        logger.info("Fetching pages from category: %s", category)
        before = len(pages)

        try:
            members = site.categories[category]
        except Exception as exc:
            logger.warning("Skipping '%s': %s", category, exc)
            continue

        for page in members:
            if getattr(page, "namespace", None) == NS_CATEGORY:
                continue
            if page.name in seen:
                continue
            seen.add(page.name)

            pages.append(
                {
                    "title": page.name,
                    "pageid": page.pageid,
                    "url": f"https://{WIKI_URL}/wiki/{page.name.replace(' ', '_')}",
                }
            )

        logger.info(
            "  +%d new pages (running total: %d)", len(pages) - before, len(pages)
        )

    logger.info(
        "Found %d unique pages across %d categories",
        len(pages),
        len(categories),
    )
    return pages


def clean_wikitext(wikitext: str) -> str:
    """
    Plain text for RAG. ``keep_template_params`` keeps infobox values
    (components, produces, …) that default ``strip_code()`` would drop.
    """
    for sep in ("<br />", "<br/>", "<br>", "<BR />", "<BR/>", "<BR>"):
        wikitext = wikitext.replace(sep, "\n")

    text = mwparserfromhell.parse(wikitext).strip_code(keep_template_params=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def fetch_page_content(site: mwclient.Site, title: str) -> str | None:
    try:
        page = site.pages[title]
        wikitext = page.text()
        if not wikitext:
            return None
        return clean_wikitext(wikitext)

    except Exception as exc:
        with _print_lock:
            logger.warning("Failed to fetch '%s': %s", title, exc)
        return None


def load_raw_page(raw_file: Path) -> dict | None:
    try:
        data = json.loads(raw_file.read_text())
        text = data.get("text")
        if not text:
            return None
        return data
    except (OSError, json.JSONDecodeError):
        return None


def chunk_text(text: str, metadata: dict) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.create_documents([text], [metadata])


class PageResult(TypedDict):
    status: str
    docs: list[Document]


def process_page(
    page: dict[str, str | int],
    index: int,
    total: int,
) -> PageResult:
    """
    Load from cache or fetch one page, then chunk.

    Returns ``{"status": "cached|fetched|failed", "docs": [...]}``.
    """
    raw_file = RAW_DATA_DIR / f"{page['pageid']}.json"
    title = str(page["title"])

    text: str | None = None
    status = "failed"

    if raw_file.exists():
        cached_page = load_raw_page(raw_file)
        if cached_page:
            text = cached_page["text"]
            status = "cached"

    if text is None:
        text = fetch_page_content(_thread_site(), title)
        if not text:
            with _print_lock:
                logger.info("[%d/%d] %s (failed)", index, total, title)
            return {"status": "failed", "docs": []}

        raw_file.write_text(
            json.dumps(
                {"title": title, "url": str(page["url"]), "text": text},
                ensure_ascii=False,
            ),
        )
        status = "fetched"

    docs = chunk_text(
        text,
        {"page_title": title, "source_url": str(page["url"])},
    )
    with _print_lock:
        logger.info(
            "[%d/%d] %s (%s, %d chunks)", index, total, title, status, len(docs)
        )
    return {"status": status, "docs": docs}


def embed_and_store(docs: list[Document]) -> None:
    """Embed chunks in batches and upsert into ChromaDB."""
    if not docs:
        logger.info("No documents to embed.")
        return

    logger.info(
        "Embedding %d chunks (provider=%s, batch=%d)…",
        len(docs),
        embedding_provider_label(),
        settings.ingest_embed_batch,
    )

    chroma_client = chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )
    embeddings = get_embeddings()

    try:
        chroma_client.delete_collection(COLLECTION_NAME)
        logger.info("Deleted existing collection '%s'", COLLECTION_NAME)
    except Exception as exc:
        logger.info("No existing collection to delete (%s)", exc)

    vectorstore = Chroma(
        client=chroma_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    collection = vectorstore._collection

    batches = [
        docs[i : i + settings.ingest_embed_batch]
        for i in range(0, len(docs), settings.ingest_embed_batch)
    ]
    stored = 0

    for batch_index, batch in enumerate(batches):
        texts = [doc.page_content for doc in batch]
        vectors = embeddings.embed_documents(texts)
        ids = [str(uuid.uuid4()) for _ in batch]
        collection.upsert(
            ids=ids,
            embeddings=vectors,  # type: ignore[arg-type]
            documents=texts,
            metadatas=[doc.metadata for doc in batch],  # type: ignore[arg-type]
        )
        stored += len(batch)
        logger.info(
            "Batch %d/%d - stored %d/%d chunks",
            batch_index + 1,
            len(batches),
            stored,
            len(docs),
        )


def main() -> None:
    logger.info("=" * 60)
    logger.info("Witcher 3 Wiki Ingest")
    logger.info("=" * 60)
    logger.info("Fetch workers: %d", settings.ingest_workers)

    site = connect_to_wiki()

    pages = get_category_pages(site, CATEGORIES)
    if not pages:
        logger.warning("No pages found. Check CATEGORIES or wiki availability.")
        return

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    docs: list[Document] = []
    fetched = 0
    cached = 0
    failed = 0
    total = len(pages)

    logger.info("Fetching + chunking with %d workers…", settings.ingest_workers)
    with ThreadPoolExecutor(max_workers=settings.ingest_workers) as pool:
        futures = {
            pool.submit(process_page, page, i + 1, total): page
            for i, page in enumerate(pages)
        }
        for future in as_completed(futures):
            result = future.result()
            status = result["status"]
            if status == "cached":
                cached += 1
            elif status == "fetched":
                fetched += 1
            else:
                failed += 1
                continue
            docs.extend(result["docs"])

    logger.info(
        "Pages: %d listed | %d fetched | %d from cache | %d failed",
        total,
        fetched,
        cached,
        failed,
    )
    logger.info("Total chunks: %d", len(docs))

    embed_and_store(docs)

    logger.info("✅ Ingest complete! %d chunks indexed in ChromaDB.", len(docs))
    logger.info("   Raw data saved to data/raw/")


if __name__ == "__main__":
    main()
