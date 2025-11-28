import re


def strip_markup(text: str) -> str:
    """Remove link/inline markup like TO/TT and @TO ...@ from text."""
    if not isinstance(text, str):
        return text

    def repl_double(match):
        return match.group(1)

    # TO/TT "foo"
    text = re.sub(r'\b(?:TO|TT)\s+"([^"]+)"', repl_double, text)
    # TO/TT foo
    text = re.sub(r"\b(?:TO|TT)\s+([A-Za-z0-9_.]+)", repl_double, text)
    # @TO "foo"@ variants
    text = re.sub(r'@?TO\s+"([^"]+)"@?', repl_double, text)
    # PARA{} markers
    text = text.replace("PARA{}", "")
    return text


def clean_symbol(s: str) -> str:
    s = strip_markup(s) if isinstance(s, str) else s
    s = s.strip()
    s = re.sub(r'^[{(\s"\']+|[})"\']+$', "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()
