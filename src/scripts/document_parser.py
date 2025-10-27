import re

def extract_document_blocks(text: str):
    pattern = re.compile(r'document\s*\{', re.M)
    docs = []
    for match in pattern.finditer(text):
        start = match.end()
        depth, i = 1, start
        while i < len(text) and depth > 0:
            if text[i] == '{': depth += 1
            elif text[i] == '}': depth -= 1
            i += 1
        docs.append(text[start:i-1].strip())
    return docs

def parse_document_block(block: str):
    kv_pattern = re.compile(r'(\w+)\s*=>\s*(.*?)(?:,|$)', re.S)
    result = {}
    for key, value in kv_pattern.findall(block):
        val = value.strip()
        if val.startswith('{') and val.endswith('}'):
            val = val[1:-1].strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        result[key] = val
    return result