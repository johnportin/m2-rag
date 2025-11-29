from __future__ import annotations

from typing import List, Dict

from pydantic import BaseModel

from src.db.emb_index import create_index, EmbeddedDocIndex
from src.db.ms_index import MinsearchDocIndex

SearchIndex = EmbeddedDocIndex | MinsearchDocIndex

index: SearchIndex = create_index()
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
