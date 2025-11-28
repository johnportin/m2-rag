from src.cli.query_index import run_query, format_results
from src.db.emb_index import EmbeddedDocIndex


def test_run_query(index: EmbeddedDocIndex):
    results = run_query(index, "hash table", k=2)
    assert results, "expected results"
    assert all("score" in r for r in results)


def test_format_results(index: EmbeddedDocIndex):
    results = run_query(index, "ideal", k=1)
    rendered = format_results(results)
    assert isinstance(rendered, str)
    assert rendered
