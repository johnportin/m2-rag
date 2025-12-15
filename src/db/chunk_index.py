from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, TYPE_CHECKING

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ModuleNotFoundError:  # pragma: no cover - optional dep
    SentenceTransformer = None  # type: ignore[assignment]

try:  # optional; fallback to text search if missing
    import faiss  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - only hit in constrained envs
    faiss = None  # type: ignore[assignment]

from minsearch import Index

CHUNK_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "m2_chunks.jsonl"
DEFAULT_MODEL = os.getenv("M2_EMB_MODEL", "all-MiniLM-L6-v2")

if TYPE_CHECKING:  # type hints only
    from src.db.ms_index import MinsearchDocIndex


def load_chunks(path: Path = CHUNK_DATA_PATH) -> List[Dict]:
    docs: List[Dict] = []
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Generate chunked data with `uv run python src/scripts/chunk_docs.py`."
        )
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            if "text" not in doc:
                continue
            docs.append(doc)
    return docs


class ChunkEmbeddedIndex:
    """
    FAISS-backed embedding index over raw text chunks.
    Uses cosine similarity (inner product on normalized vectors).
    """

    def __init__(self, data_path: Path = CHUNK_DATA_PATH, model_name: str = DEFAULT_MODEL):
        if SentenceTransformer is None:  # pragma: no cover - guarded by create_index
            raise RuntimeError("sentence-transformers is unavailable; cannot build chunk embeddings.")
        self.data_path = Path(data_path)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        self.docs = load_chunks(self.data_path)
        if not self.docs:
            self.index = None
            return

        texts = [doc.get("text", "") for doc in self.docs]
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        if faiss is None:  # pragma: no cover - guarded by create_index
            raise RuntimeError("faiss is unavailable; cannot build embedding index.")

        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        if not query or not self.docs or self.index is None:
            return []

        query_vec = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        k = min(k, len(self.docs))
        scores, indices = self.index.search(query_vec, k)

        results: List[Dict] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue
            doc = dict(self.docs[idx])
            doc["score"] = float(score)
            results.append(doc)
        return results


class ChunkMinsearchIndex:
    """
    Text-only search index over chunks using minsearch.
    """

    def __init__(self, data_path: Path = CHUNK_DATA_PATH):
        self.data_path = Path(data_path)
        self.docs = load_chunks(self.data_path)
        if not self.docs:
            self.index = None
            return

        text_fields = ["text"]
        keyword_fields = ["source"]
        self.index = Index(text_fields=text_fields, keyword_fields=keyword_fields)
        self.index.fit(self.docs)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        if not query or not self.index:
            return []
        return self.index.search(query, num_results=k)


def create_index(
    data_path: Path = CHUNK_DATA_PATH,
    model_name: str = DEFAULT_MODEL,
) -> ChunkEmbeddedIndex | ChunkMinsearchIndex:
    if faiss is None or SentenceTransformer is None:
        return ChunkMinsearchIndex(data_path=data_path)
    return ChunkEmbeddedIndex(data_path=data_path, model_name=model_name)
