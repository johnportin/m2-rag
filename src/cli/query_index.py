from __future__ import annotations

from __future__ import annotations

from pathlib import Path
from typing import List

from src.cli.search_common import SearchBackend, run_search_cli
from src.db.emb_index import EmbeddedDocIndex, create_index, DATA_PATH, DEFAULT_MODEL


def format_results(results: List[dict]) -> str:
    lines = []
    for i, doc in enumerate(results, start=1):
        headline = doc.get("headline") or doc.get("usage") or doc.get("keys") or "<no title>"
        source = doc.get("source", "<unknown source>")
        score = doc.get("score", 0.0)
        lines.append(f"{i}. {headline} (source: {source}, score: {score:.4f})")
    return "\n".join(lines) if lines else "No results."


def run_query(index: EmbeddedDocIndex, query: str, k: int) -> List[dict]:
    """Backward-compatible wrapper for tests."""
    return index.search(query, k=k)


def print_results(results: List[dict], show_scores: bool) -> None:
    if show_scores:
        print(format_results(results))
        return
    for i, doc in enumerate(results, start=1):
        headline = doc.get("headline") or doc.get("usage") or doc.get("keys") or "<no title>"
        source = doc.get("source", "<unknown source>")
        print(f"{i}. {headline} (source: {source})")


backend = SearchBackend(
    description="Search the M2 docs embedding index (FAISS).",
    default_data_path=DATA_PATH,
    default_model=DEFAULT_MODEL,
    create_index=lambda data_path, model: create_index(data_path, model_name=model or DEFAULT_MODEL),
    print_results=print_results,
)


def main() -> None:
    run_search_cli(backend)


if __name__ == "__main__":
    main()
