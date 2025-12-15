from __future__ import annotations

from __future__ import annotations

from typing import List

from src.cli.search_common import SearchBackend, run_search_cli
from src.db.chunk_index import ChunkEmbeddedIndex, ChunkMinsearchIndex, CHUNK_DATA_PATH, DEFAULT_MODEL, create_index


def format_results(results: List[dict]) -> str:
    lines = []
    for i, doc in enumerate(results, start=1):
        source = doc.get("source", "<unknown source>")
        score = doc.get("score")
        preview = (doc.get("text") or "").strip()
        preview = preview[:160] + ("..." if len(preview) > 160 else "")
        if score is not None:
            lines.append(f"{i}. {preview} (source: {source}, score: {float(score):.4f})")
        else:
            lines.append(f"{i}. {preview} (source: {source})")
    return "\n".join(lines) if lines else "No results."


def run_query(index: ChunkEmbeddedIndex | ChunkMinsearchIndex, query: str, k: int) -> List[dict]:
    """Backward-compatible wrapper for tests."""
    return index.search(query, k=k)


def print_results(results: List[dict], show_scores: bool) -> None:
    if show_scores:
        print(format_results(results))
        return
    for i, doc in enumerate(results, start=1):
        source = doc.get("source", "<unknown source>")
        preview = (doc.get("text") or "").strip()
        preview = preview[:160] + ("..." if len(preview) > 160 else "")
        print(f"{i}. {preview} (source: {source})")


backend = SearchBackend(
    description="Search the chunk-based embedding/text index.",
    default_data_path=CHUNK_DATA_PATH,
    default_model=DEFAULT_MODEL,
    create_index=lambda data_path, model: create_index(data_path, model_name=model or DEFAULT_MODEL),
    print_results=print_results,
)


def main() -> None:
    run_search_cli(backend)


if __name__ == "__main__":
    main()
