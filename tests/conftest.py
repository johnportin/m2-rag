import os
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

os.environ.setdefault("OPENAI_API_KEY", "test")

from src.agents.judge_agent import judge_agent
from src.agents.rag_agent import rag_agent
from src.db.emb_index import create_index as create_emb_index, EmbeddedDocIndex
from src.db.ms_index import create_index as create_ms_index, MinsearchDocIndex


@pytest.fixture(scope="session")
def data_path() -> Path:
    path = Path(__file__).resolve().parent.parent / "data" / "m2_docs.jsonl"
    if not path.exists():
        pytest.skip("data/m2_docs.jsonl is missing; run data prep scripts first.")
    return path


@pytest.fixture(scope="session")
def index(data_path: Path) -> EmbeddedDocIndex:
    try:
        return create_emb_index(data_path)
    except OSError as exc:
        pytest.skip(f"Model unavailable or failed to load embeddings: {exc}")


@pytest.fixture(scope="session")
def ms_index(data_path: Path) -> MinsearchDocIndex:
    return create_ms_index(data_path)


@pytest.fixture()
def test_rag_agent():
    """
    Provide a deterministic version of the RAG agent that forces tool execution.
    This avoids real OpenAI calls while still exercising the agent plumbing.
    """
    test_model = TestModel(
        call_tools="all",
        custom_output_args={
            "answer": "(test complete)",
            "references": ["[test_source] synthetic reference"],
        },
    )
    with rag_agent.override(model=test_model):
        yield rag_agent


@pytest.fixture()
def test_judge_agent():
    """Yield the judge agent backed by a deterministic TestModel."""
    test_model = TestModel(
        custom_output_args={
            "decision": "pass",
            "score": 0.75,
            "rationale": "Answer satisfies rubric in this test stub.",
            "required_improvements": [],
        }
    )
    with judge_agent.override(model=test_model):
        yield judge_agent
