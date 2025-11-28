import re
from typing import List, Dict

from src.m2rag.ingest.doc_blocks import parse_doc_blocks
from src.m2rag.ingest.document_blocks import extract_document_blocks, parse_document_block
from src.m2rag.ingest.reader import read_m2_files, M2File
from src.m2rag.ingest.utils import clean_symbol, strip_markup


def _normalize_entry(raw: Dict, source: str, syntax: str) -> Dict:
    raw = dict(raw)
    raw.pop("Subnodes", None)  # drop nav structure

    # Clean markup from all string fields early
    for k, v in list(raw.items()):
        if isinstance(v, str):
            raw[k] = strip_markup(v)
        elif isinstance(v, list):
            raw[k] = [strip_markup(item) if isinstance(item, str) else item for item in v]

    def _split_lines(val: str):
        return [clean_symbol(k) for k in re.split(r"[\\n,]+", val) if k.strip()]

    keys_val = raw.get("Key", "")
    keys = keys_val if isinstance(keys_val, list) else _split_lines(keys_val)

    desc_parts = [raw.get("Description", "").strip(), raw.get("Text", "").strip()]
    description = "\\n".join([p for p in desc_parts if p])
    if isinstance(description, str):
        description = strip_markup(description)
        description = re.sub(r'\s*"\s*,?\s*', " ", description)
        description = re.sub(r"\s*,\s*\.", ".", description)
        description = re.sub(r"\s*,\s*", ", ", description)
        description = " ".join(description.split())

    seealso_raw = raw.get("SeeAlso", [])
    if isinstance(seealso_raw, str):
        seealso = _split_lines(seealso_raw)
    else:
        seealso = [clean_symbol(s) for s in seealso_raw if str(s).strip()]

    entry = {
        "keys": keys,
        "headline": raw.get("Headline", "").strip(),
        "usage": raw.get("Usage", "").strip(),
        "description": description,
        "examples": raw.get("Example", "").strip(),
        "seealso": seealso,
        "source": source,
        "syntax": syntax,
    }

    for field, default in [
        ("keys", []),
        ("headline", ""),
        ("usage", ""),
        ("description", ""),
        ("examples", ""),
        ("seealso", []),
    ]:
        if entry.get(field) is None:
            entry[field] = default
    return entry


def validate_docs(docs: List[Dict], source: str, warn_counter: List[int] | None = None) -> List[Dict]:
    """Ensure fields exist and log any entries missing core data."""
    required_fields = ["keys", "headline", "usage", "description", "examples", "seealso", "source", "syntax"]
    for i, doc in enumerate(docs):
        for field in required_fields:
            if field not in doc:
                doc[field] = [] if field in ("keys", "seealso") else ""
        if not doc.get("headline") and not doc.get("description"):
            print(f"[WARN] Missing headline/description in {source} (entry #{i}, syntax={doc.get('syntax')})")
            if warn_counter is not None:
                warn_counter[0] += 1
    return docs


def parse_m2_file(m2file: M2File, warn_counter: List[int] | None = None) -> List[Dict]:
    docs: List[Dict] = []

    for entry in parse_doc_blocks(m2file.content):
        docs.append(_normalize_entry(entry, m2file.path, syntax="doc"))

    for block in extract_document_blocks(m2file.content):
        entry = parse_document_block(block)
        docs.append(_normalize_entry(entry, m2file.path, syntax="document"))

    return validate_docs(docs, source=m2file.path, warn_counter=warn_counter)


def parse_all_docs(root_dir: str, with_stats: bool = False):
    warn_counter = [0]
    all_docs: List[Dict] = []
    for m2file in read_m2_files(root_dir):
        all_docs.extend(parse_m2_file(m2file, warn_counter=warn_counter))
    if with_stats:
        return all_docs, warn_counter[0]
    return all_docs
