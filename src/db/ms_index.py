from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from minsearch import Index

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "m2_docs.jsonl"


def _normalize_doc(doc: Dict) -> Dict:
    normalized = dict(doc)
    if isinstance(normalized.get("keys"), list):
        normalized["keys"] = " ".join(normalized["keys"])

    for field in ["keys", "headline", "usage", "description", "examples"]:
        val = normalized.get(field, "")
        if val is None:
            normalized[field] = ""
        elif isinstance(val, str):
            normalized[field] = val.lower()
    return normalized


def load_docs(path: Path = DATA_PATH) -> List[Dict]:
    docs: List[Dict] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            docs.append(_normalize_doc(doc))
    return docs


class MinsearchDocIndex:
    """
    Text-only search index backed by minsearch.
    Kept structurally similar to EmbeddedDocIndex for easy swapping.
    """

    def __init__(self, data_path: Path = DATA_PATH):
        self.data_path = Path(data_path)
        self.docs = load_docs(self.data_path)
        if not self.docs:
            self.index = None
            return

        text_fields = ["keys", "usage", "description", "headline", "examples"]
        keyword_fields = ["source"]

        self.index = Index(text_fields=text_fields, keyword_fields=keyword_fields)
        self.index.fit(self.docs)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        if not query or not self.index:
            return []
        return self.index.search(query, num_results=k)


def create_index(data_path: Path = DATA_PATH) -> MinsearchDocIndex:
    return MinsearchDocIndex(data_path=data_path)
