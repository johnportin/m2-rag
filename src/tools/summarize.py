from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.tools.search import get_last_search_results


class SummarizeDocsArgs(BaseModel):
    # Default to None to avoid accidental mutation across requests.
    docs: Optional[List[Dict]] = Field(default=None)


def summarize_docs(args: SummarizeDocsArgs) -> str:
    docs = args.docs or get_last_search_results()

    if not docs:
        return "No relevant documentation found."

    summary_blocks: List[str] = []
    for doc in docs[:5]:
        headline = (doc.get("headline") or doc.get("usage") or "Untitled").strip()
        description = (doc.get("description") or "").strip()
        bullet = f"- **{headline}**"
        if description:
            bullet += f" {description}"
        summary_blocks.append(bullet)

    return "Here are the most relevant documentation details:\n" + "\n".join(summary_blocks)
