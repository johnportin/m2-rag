"""
Create simple text chunks from raw Macaulay2 docs for embedding-based search.

Example:
    uv run python src/scripts/chunk_docs.py --root data/macaulay2docs --output data/m2_chunks.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Tuple

from src.m2rag.ingest.reader import read_m2_files


def chunk_tokens(tokens: List[str], max_tokens: int, overlap: int) -> Iterable[Tuple[str, int, int]]:
    """
    Yield (chunk_text, start_idx, end_idx) with simple fixed-size token windows.
    Overlap keeps neighboring context.
    """
    step = max_tokens - overlap
    if step <= 0:
        raise ValueError("overlap must be smaller than max_tokens")

    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + max_tokens)
        yield " ".join(tokens[start:end]), start, end
        if end == len(tokens):
            break
        start = end - overlap


def build_chunks(root: Path, max_tokens: int, overlap: int) -> Iterable[dict]:
    """
    Read .m2 files and produce chunk dicts with text and metadata.
    """
    for m2file in read_m2_files(str(root)):
        tokens = m2file.content.split()
        for idx, (chunk, start, end) in enumerate(chunk_tokens(tokens, max_tokens, overlap)):
            yield {
                "text": chunk,
                "source": m2file.path,
                "chunk_id": idx,
                "token_start": start,
                "token_end": end,
            }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chunk raw .m2 docs for embedding search.")
    parser.add_argument("--root", type=Path, default=Path("data") / "macaulay2docs", help="Path to raw .m2 docs root.")
    parser.add_argument("--output", type=Path, default=Path("data") / "m2_chunks.jsonl", help="Output jsonl path.")
    parser.add_argument("--max-tokens", type=int, default=200, help="Max tokens per chunk (default: 200).")
    parser.add_argument("--overlap", type=int, default=40, help="Token overlap between chunks (default: 40).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as f:
        count = 0
        for chunk in build_chunks(args.root, args.max_tokens, args.overlap):
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            count += 1

    print(f"Wrote {count} chunks to {args.output}")


if __name__ == "__main__":
    main()
