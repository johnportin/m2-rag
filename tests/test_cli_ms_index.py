from src.cli.query_ms_index import run_query, format_results
from src.db.ms_index import MinsearchDocIndex


def test_run_query(ms_index: MinsearchDocIndex):
    results = run_query(ms_index, "hash table", k=2)
    assert results, "expected results"


def test_format_results(ms_index: MinsearchDocIndex):
    results = run_query(ms_index, "ideal", k=1)
    rendered = format_results(results)
    assert isinstance(rendered, str)
    assert rendered
