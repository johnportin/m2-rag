from typing import List, Dict
from pydantic import BaseModel

class SummarizeDocsArgs(BaseModel):
    docs: List[Dict] = []

def summarize_docs(args: SummarizeDocsArgs) -> str:
    docs = args.docs

    if not docs:
        return "No relevant documentation found."

    summary_blocks = []
    for d in docs[:5]:
        headline = d.get("headline", "Untitled")
        description = d.get("description", "").strip()
        summary_blocks.append(f"• **{headline}** — {description}")

    return "Here are the most relevant documentation details:\n" + "\n".join(summary_blocks)
