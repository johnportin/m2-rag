from __future__ import annotations

from src.tools.search import SearchDocsArgs, get_last_search_results, search_docs
from src.tools.summarize import SummarizeDocsArgs, summarize_docs


def test_search_caches_last_results():
    search_docs(SearchDocsArgs(query="ideal", k=2))
    cached = get_last_search_results()

    assert cached, "search_docs should cache last search results"
    assert len(cached) <= 2


def test_summarize_uses_cached_results_when_missing_docs():
    search_docs(SearchDocsArgs(query="ideal", k=1))
    summary = summarize_docs(SummarizeDocsArgs())  # intentionally omit docs

    assert "Here are the most relevant documentation details" in summary
    assert "- **" in summary
