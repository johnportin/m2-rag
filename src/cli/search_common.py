from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol


class SupportsSearch(Protocol):
    def search(self, query: str, k: int) -> list[dict]:
        ...


IndexFactory = Callable[[Path, str | None], SupportsSearch]
PrintResults = Callable[[list[dict], bool], None]


@dataclass
class SearchBackend:
    """Configuration for a search CLI backend."""

    description: str
    default_data_path: Path
    default_model: str | None
    create_index: IndexFactory
    print_results: PrintResults


def add_common_args(parser: argparse.ArgumentParser, backend: SearchBackend) -> argparse.ArgumentParser:
    parser.add_argument("query", nargs="?", help="Search query text.")
    parser.add_argument("-k", type=int, default=5, help="Number of results to return (default: 5).")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=backend.default_data_path,
        help=f"Path to data file (default: {backend.default_data_path})",
    )
    if backend.default_model is not None:
        parser.add_argument(
            "--model",
            default=backend.default_model,
            help=f"SentenceTransformer model name (default: {backend.default_model})",
        )
    parser.add_argument(
        "--show-scores",
        action="store_true",
        help="Include similarity scores in output.",
    )
    return parser


def run_search_cli(backend: SearchBackend) -> None:
    parser = argparse.ArgumentParser(description=backend.description)
    parser = add_common_args(parser, backend)
    args = parser.parse_args()

    if not args.query:
        raise SystemExit(
            "Please provide a query (see --help for usage), e.g. `uv run python -m src.cli.query_index \"hilbert polynomial\"`"
        )

    model_arg = getattr(args, "model", None)
    index = backend.create_index(args.data_path, model_arg)
    results = index.search(args.query, k=args.k)
    backend.print_results(results, args.show_scores)
