from __future__ import annotations

import requests
from pydantic import BaseModel, Field


class SearchWikipediaArgs(BaseModel):
    query: str = Field(..., description="Topic to search on Wikipedia.")
    limit: int = Field(3, ge=1, le=10, description="Maximum number of results to return.")


def search_wikipedia(args: SearchWikipediaArgs) -> list[dict]:
    """
    Search Wikipedia and return basic snippets for the top results.
    """
    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srlimit": args.limit,
        "srsearch": args.query,
        "origin": "*",  # CORS-friendly and required by some gateways
    }
    headers = {
        # Wikipedia requires an identifying User-Agent per https://meta.wikimedia.org/wiki/User-Agent_policy
        "User-Agent": "m2-rag/0.1 (contact: jportin13@gmail.com)",
    }
    try:
        resp = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        return [
            {
                "title": "Wikipedia search failed",
                "snippet": f"HTTP error: {exc}",
                "url": "",
                "source": "Wikipedia",
            }
        ]
    data = resp.json()
    results = data.get("query", {}).get("search", []) or []

    cleaned = []
    for item in results:
        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
        cleaned.append(
            {
                "title": title,
                "snippet": snippet,
                "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "source": f"Wikipedia: {title}",
            }
        )
    return cleaned
