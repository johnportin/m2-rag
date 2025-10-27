from reader import read_m2_files, M2File
from doc_parser import parse_doc_blocks
from document_parser import extract_document_blocks, parse_document_block
from parsing_utils import clean_symbol

def parse_m2_file(m2file: M2File):
    docs = []

    # doc-style
    for entry in parse_doc_blocks(m2file.content):
        docs.append({
            "keys": [clean_symbol(k) for k in entry.get("Key", "").splitlines() if k.strip()],
            "headline": entry.get("Headline", "").strip(),
            "usage": entry.get("Usage", "").strip(),
            "description": entry.get("Description", "").strip(),
            "examples": entry.get("Example", "").strip(),
            "seealso": [clean_symbol(s) for s in entry.get("SeeAlso", "").split(",") if s.strip()],
            "source": m2file.path,
            "syntax": "doc"
        })

    # document-style
    for block in extract_document_blocks(m2file.content):
        entry = parse_document_block(block)
        docs.append({
            "keys": [clean_symbol(k) for k in entry.get("Key", "").split(",") if k.strip()],
            "headline": entry.get("Headline", "").strip(),
            "usage": entry.get("Usage", "").strip(),
            "description": entry.get("Description", "").strip(),
            "examples": entry.get("Example", "").strip(),
            "seealso": [clean_symbol(s) for s in entry.get("SeeAlso", "").split(",") if s.strip()],
            "source": m2file.path,
            "syntax": "document"
        })

    return docs

def parse_all_docs(root_dir: str):
    all_docs = []
    for m2file in read_m2_files(root_dir):
        all_docs.extend(parse_m2_file(m2file))
    return all_docs
