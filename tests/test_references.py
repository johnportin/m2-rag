from __future__ import annotations


def test_response_contains_references(test_rag_agent):
    result = test_rag_agent.run_sync("What is a monomial ideal?")
    body = result.output.answer

    assert body, "Agent response should not be empty."
    assert result.output.references, "Expected at least one reference entry."
