import re

from src.m2rag.ingest.constants import SECTION_NAMES


def parse_doc_blocks(text: str):
    """
    Parse `doc/// ... ///` blocks. Handles labeled sections with optional
    indentation (e.g., Key/Headline/Usage/Description/Example/SeeAlso/Text).
    """
    blocks = re.findall(r"doc\s*///(.*?)///", text, flags=re.S)
    section_pattern = re.compile(
        rf"^\s*(?P<section>{'|'.join(SECTION_NAMES)})\s*\n(.*?)(?=^\s*(?:{'|'.join(SECTION_NAMES)})\s*\n|\Z)",
        re.S | re.M,
    )

    results = []
    for block in blocks:
        entry = {}
        for match in section_pattern.finditer(block.strip()):
            name = match.group("section").strip()
            content = match.group(2).strip()
            entry[name] = content
        results.append(entry)
    return results
