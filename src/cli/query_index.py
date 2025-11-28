from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from src.db.emb_index import (
    EmbeddedDocIndex,
    create_index,
    DATA_PATH,
    DEFAULT_MODEL,
)


def run_query(index: EmbeddedDocIndex, query: str, k: int) -> List[dict]:
    """Execute a search and return results (kept raw for flexibility)."""
    return index.search(query, k=k)


def format_results(results: List[dict]) -> str:
    lines = []
    for i, doc in enumerate(results, start=1):
        headline = doc.get("headline") or doc.get("usage") or doc.get("keys") or "<no title>"
        source = doc.get("source", "<unknown source>")
        score = doc.get("score", 0.0)
        lines.append(f"{i}. {headline} (source: {source}, score: {score:.4f})")
    return "\n".join(lines) if lines else "No results."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search the M2 docs embedding index (FAISS).",
    )
    parser.add_argument("query", nargs="?", help="Search query text.")
    parser.add_argument("-k", type=int, default=5, help="Number of results to return (default: 5).")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DATA_PATH,
        help=f"Path to m2_docs.jsonl (default: {DATA_PATH})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"SentenceTransformer model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--show-scores",
        action="store_true",
        help="Include similarity scores in output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.query:
        raise SystemExit("Please provide a query, e.g. `uv run python -m src.cli.query_index \"hilbert polynomial\"`")

    index = create_index(args.data_path, model_name=args.model)
    results = run_query(index, args.query, k=args.k)

    if args.show_scores:
        print(format_results(results))
    else:
        for i, doc in enumerate(results, start=1):
            headline = doc.get("headline") or doc.get("usage") or doc.get("keys") or "<no title>"
            source = doc.get("source", "<unknown source>")
            print(f"{i}. {headline} (source: {source})")


if __name__ == "__main__":
    main()
