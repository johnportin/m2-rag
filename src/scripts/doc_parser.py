import re
from parsing_utils import SECTION_NAMES

def parse_doc_blocks(text: str):
    blocks = re.findall(r'doc\s*///(.*?)///', text, flags=re.S)
    section_pattern = re.compile(
        rf'(?P<section>{"|".join(SECTION_NAMES)})\s*\n(.*?)(?=(?:\n(?:{"|".join(SECTION_NAMES)})\s*\n)|\Z)',
        re.S
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