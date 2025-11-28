from pathlib import Path

import pytest

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
