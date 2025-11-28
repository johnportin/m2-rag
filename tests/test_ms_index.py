from src.db.ms_index import MinsearchDocIndex


def test_ms_index_builds(ms_index: MinsearchDocIndex):
    assert isinstance(ms_index, MinsearchDocIndex)
    assert ms_index.docs
    assert ms_index.index is not None


def test_ms_search_returns_results(ms_index: MinsearchDocIndex):
    results = ms_index.search("hash table", k=3)
    assert isinstance(results, list)
    assert results, "expected at least one search result"
    for result in results:
        assert "source" in result
        assert isinstance(result.get("description", ""), str)
