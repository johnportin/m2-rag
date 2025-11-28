from src.db.emb_index import EmbeddedDocIndex


def test_index_builds(index: EmbeddedDocIndex):
    assert isinstance(index, EmbeddedDocIndex)
    assert index.docs
    assert index.index is not None


def test_search_returns_results(index: EmbeddedDocIndex):
    results = index.search("hash table", k=3)
    assert isinstance(results, list)
    assert results, "expected at least one search result"
    for result in results:
        assert "source" in result
        assert isinstance(result.get("description", ""), str)
        assert "score" in result
