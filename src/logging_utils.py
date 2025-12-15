from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


def log_event(
    event: dict[str, Any],
    *,
    path: str | Path | None = None,
    run_id: Optional[str] = None,
) -> None:
    """Append a structured event to a JSONL log."""
    log_path = Path(path or os.getenv("LOG_PATH", "logs/runs.jsonl"))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "run_id": run_id or str(uuid4()),
        **event,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

