import re

SECTION_NAMES = [
    "Key", "Headline", "Usage", "Description", "Example", "SeeAlso",
    "Text", "Subnodes", "Caveat", "Synopsis", "Returns", "Notes"
]

def clean_symbol(s: str) -> str:
    s = s.strip()
    s = re.sub(r'^[{(\s"\']+|[})"\']+$', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()