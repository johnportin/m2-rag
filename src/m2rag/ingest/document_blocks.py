import re
from typing import Dict, List

from src.m2rag.ingest.utils import clean_symbol, strip_markup


def extract_document_blocks(text: str) -> List[str]:
    pattern = re.compile(r"document\s*\{", re.M)
    docs = []
    for match in pattern.finditer(text):
        start = match.end()
        depth, i = 1, start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        docs.append(text[start : i - 1].strip())
    return docs


def _split_value_list(val: str) -> List[str]:
    return [clean_symbol(v) for v in re.split(r"[,\\n]+", val) if v.strip()]


def parse_document_block(block: str) -> Dict[str, str | List[str]]:
    """
    Parse a `document { ... }` block. Values may be scalars or lists.
    """
    lines = block.splitlines()
    result: Dict[str, str | List[str]] = {}
    free_text: List[str] = []

    current_key = None
    buffer: List[str] = []
    collecting_list = False

    def flush(key: str, buf: List[str]):
        val = "\n".join(buf).strip().rstrip(",")
        if not val:
            return
        val = strip_markup(val)
        if val.startswith("{") and val.endswith("}"):
            inner = val[1:-1].strip()
            result[key] = _split_value_list(inner)
        else:
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            result[key] = val.strip()

    for line in lines:
        stripped = line.strip()
        if "=>" in line:
            maybe_key, rest = line.split("=>", 1)
            key_candidate = maybe_key.strip()
            if key_candidate.isidentifier():
                # flush previous
                if current_key:
                    flush(current_key, buffer)
                current_key = key_candidate
                buffer = [rest.strip()]
                collecting_list = buffer[0].startswith("{") and not buffer[0].endswith("}")
                # If value likely ends on this line, flush immediately
                if not collecting_list and not buffer[0].endswith("\\"):
                    flush(current_key, buffer)
                    current_key = None
                    buffer = []
                continue
        # not a new key line
        if current_key:
            buffer.append(stripped)
            if collecting_list and "}" in stripped:
                flush(current_key, buffer)
                current_key = None
                buffer = []
                collecting_list = False
        else:
            if stripped:
                free_text.append(strip_markup(stripped))

    if current_key:
        flush(current_key, buffer)

    if free_text:
        desc = result.get("Description", "")
        combined = "\n".join([desc, *free_text]).strip() if desc else "\n".join(free_text).strip()
        result["Description"] = strip_markup(combined)

    return result
