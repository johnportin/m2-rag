from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List, Dict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = os.getenv("M2_EMB_MODEL", "all-MiniLM-L6-v2")
DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "m2_docs.jsonl"


def _normalize_doc(doc: Dict) -> Dict:
    """Normalize a raw document row from the jsonl file."""
    normalized = dict(doc)
    if isinstance(normalized.get("keys"), list):
        normalized["keys"] = " ".join(normalized["keys"])

    for field in ["keys", "headline", "usage", "description", "examples"]:
        value = normalized.get(field, "")
        if value is None:
            normalized[field] = ""
        elif isinstance(value, str):
            normalized[field] = value
    return normalized


def _combine_text(doc: Dict) -> str:
    parts = []
    for field in ["headline", "usage", "description", "examples", "keys"]:
        val = doc.get(field, "")
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    # fall back to source if everything else is empty
    if not parts and doc.get("source"):
        parts.append(str(doc["source"]))
    return " ".join(parts)


def load_docs(path: Path = DATA_PATH) -> List[Dict]:
    docs: List[Dict] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            docs.append(_normalize_doc(doc))
    return docs


class EmbeddedDocIndex:
    """
    Simple FAISS-backed embedding index for documentation search.
    Builds embeddings once at init and searches with cosine similarity (via inner product on normalized vectors).
    """

    def __init__(self, data_path: Path = DATA_PATH, model_name: str = DEFAULT_MODEL):
        self.data_path = Path(data_path)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        self.docs = load_docs(self.data_path)
        if not self.docs:
            self.index = None
            return

        texts = [_combine_text(doc) for doc in self.docs]
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

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


def create_index(data_path: Path = DATA_PATH, model_name: str = DEFAULT_MODEL) -> EmbeddedDocIndex:
    return EmbeddedDocIndex(data_path=data_path, model_name=model_name)
