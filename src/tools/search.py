from __future__ import annotations

import os
from typing import List, Dict

from pydantic import BaseModel

from src.db.chunk_index import ChunkEmbeddedIndex, ChunkMinsearchIndex, create_index as create_chunk_index
from src.db.emb_index import EmbeddedDocIndex, create_index as create_doc_index
from src.db.ms_index import MinsearchDocIndex

SearchIndex = EmbeddedDocIndex | MinsearchDocIndex | ChunkEmbeddedIndex | ChunkMinsearchIndex


def _build_index() -> SearchIndex:
    """
    Choose which index to load based on M2_INDEX_MODE.
    - "chunks": use chunked raw doc index (data/m2_chunks.jsonl).
    - default: structured doc index (data/m2_docs.jsonl).
    """
    mode = os.getenv("M2_INDEX_MODE", "docs").lower()
    if mode in {"chunk", "chunks"}:
        return create_chunk_index()
    return create_doc_index()


index: SearchIndex = _build_index()
_last_search_results: List[Dict] = []


class SearchDocsArgs(BaseModel):
    query: str
    k: int = 5


def search_docs(args: SearchDocsArgs) -> List[Dict]:
    """
    Execute a semantic search and cache the most recent results.
    The cache lets downstream tools (like summarize_docs) reuse the latest docs.
    """
    global _last_search_results
    results = index.search(args.query, k=args.k)
    # store a shallow copy so callers cannot mutate our cache in place
    _last_search_results = list(results)
    return results


def get_last_search_results() -> List[Dict]:
    """Return the cached results from the most recent search, if any."""
    return list(_last_search_results)
