"""
Run prompts through the RAG agent and evaluate them with the judge agent.

Usage examples:
    python scripts/run_judged_prompts.py --prompt "What is a monomial ideal?"
    python scripts/run_judged_prompts.py --input prompts.json

When --input is supplied, it should point to a JSON file containing either a
list of prompt strings or an object with a top-level "prompts" array. Results
are written to output/judged_prompts_<timestamp>.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import is_dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.agents.judge_agent import build_judge_prompt, judge_agent
from src.logging_utils import log_event


def _ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY must be set to run real agent calls.")


def _load_prompts_from_file(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "prompts" in data and isinstance(data["prompts"], Iterable):
        items = data["prompts"]
    else:
        raise ValueError(f"Unsupported prompt file format in {path}")
    prompts: List[str] = []
    for item in items:
        if isinstance(item, str) and item.strip():
            prompts.append(item.strip())
    return prompts


def _parse_prompts(args: argparse.Namespace) -> List[str]:
    prompts: List[str] = []
    if args.prompt:
        prompts.extend(p for p in args.prompt if p.strip())
    if args.input:
        prompts.extend(_load_prompts_from_file(Path(args.input)))
    # remove duplicates while preserving order
    seen = set()
    deduped: List[str] = []
    for prompt in prompts:
        key = prompt.strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)
    if not deduped:
        raise ValueError("At least one prompt must be provided.")
    return deduped


def _serialize_content(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _serialize_content(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_content(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if is_dataclass(obj):
        return asdict(obj)
    return str(obj)


def _extract_tool_events(result) -> List[dict[str, Any]]:
    messages = result.all_messages() if callable(getattr(result, "all_messages", None)) else result.all_messages
    events: List[dict[str, Any]] = []
    for message in messages:
        role = getattr(message, "role", None)
        tool_name = getattr(message, "tool_name", None) or getattr(message, "name", None)
        if tool_name and role in (None, "assistant", "assistant_tool_call"):
            args = getattr(message, "args", None) or getattr(message, "tool_args", None)
            events.append(
                {
                    "type": "tool_request",
                    "name": tool_name,
                    "args": _serialize_content(args),
                }
            )
        elif role == "tool":
            content = getattr(message, "content", None)
            events.append(
                {
                    "type": "tool_response",
                    "name": tool_name or getattr(message, "name", None) or "<unknown>",
                    "content": _serialize_content(content),
                }
            )
    return events


_rag_agent = None


def get_rag_agent(index_mode: str | None):
    global _rag_agent
    if _rag_agent is None:
        if index_mode:
            os.environ["M2_INDEX_MODE"] = index_mode
        else:
            os.environ.setdefault("M2_INDEX_MODE", "chunks")
        from src.agents.rag_agent import rag_agent as _ra

        _rag_agent = _ra
    return _rag_agent


def run_prompt(prompt: str, rag_agent) -> dict[str, Any]:
    try:
        rag_result = rag_agent.run_sync(prompt)
    except Exception as exc:  # noqa: BLE001
        error_msg = f"rag_agent error: {exc}"
        log_event(
            {"event": "judged_prompt_error", "query": prompt, "error": error_msg},
            path=os.getenv("JUDGE_LOG_PATH", "logs/judge.jsonl"),
        )
        return {"query": prompt, "error": error_msg}

    rag_output = rag_result.output
    tool_events = _extract_tool_events(rag_result)

    judge_prompt = build_judge_prompt(
        question=prompt,
        answer=rag_output.answer,
        references=rag_output.references,
        tool_notes=[event["name"] for event in tool_events if event["type"] == "tool_request"],
    )
    judge_result = judge_agent.run_sync(judge_prompt)
    verdict = judge_result.output

    result = {
        "query": prompt,
        "response": rag_output.answer,
        "references": rag_output.references,
        "tool_events": tool_events,
        "judge": verdict.model_dump(),
    }
    log_event(
        {
            "event": "judged_prompt",
            "query": prompt,
            "response": rag_output.answer,
            "references": rag_output.references,
            "tool_events": tool_events,
            "judge": verdict.model_dump(),
        },
        path=os.getenv("JUDGE_LOG_PATH", "logs/judge.jsonl"),
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run prompts through RAG + judge agents.")
    parser.add_argument(
        "--prompt",
        action="append",
        help="Prompt to run (can be provided multiple times).",
    )
    parser.add_argument(
        "--input",
        help="Path to a JSON file containing prompts (list or {'prompts': [...]})",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to output/judged_prompts_<timestamp>.jsonl",
    )
    parser.add_argument(
        "--index-mode",
        choices=["docs", "chunks"],
        help="Index mode for RAG agent (overrides M2_INDEX_MODE).",
    )
    args = parser.parse_args(argv)

    _ensure_api_key()
    prompts = _parse_prompts(args)
    rag_agent = get_rag_agent(args.index_mode)

    output_path = Path(args.output) if args.output else Path("output") / f"judged_prompts_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary: list[dict[str, Any]] = []
    for prompt in prompts:
        print(f"Running prompt: {prompt}")
        result = run_prompt(prompt, rag_agent)
        summary.append(result)
        with output_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        if "error" in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Judge decision: {result['judge']['decision']} (score={result['judge']['score']:.2f})")

    print(f"\nSaved {len(summary)} results to {output_path}")


if __name__ == "__main__":
    main()
