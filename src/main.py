from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from typing import List, Optional

from jaxn import JSONParserHandler, StreamingJSONParser
from pydantic_ai import messages as ai_messages, usage as ai_usage
from pydantic_ai.run import AgentRunResultEvent

from src.logging_utils import log_event


def print_tool_calls(result) -> None:
    """Print which tools were called during the run (names only)."""
    msgs = result.all_messages() if callable(getattr(result, "all_messages", None)) else result.all_messages

    requests = []
    responses = []

    for m in msgs:
        role = getattr(m, "role", None)
        tool_name = getattr(m, "tool_name", None) or getattr(m, "name", None)
        parts = getattr(m, "parts", None) or []

        if tool_name and role in (None, "assistant", "assistant_tool_call"):
            requests.append(tool_name)
        if role == "tool":
            responses.append(tool_name or "<unknown>")

        # Also inspect message parts
        for p in parts:
            pname = getattr(p, "tool_name", None)
            if pname and getattr(p, "__class__", None).__name__ == "ToolCallPart":
                requests.append(pname)
            if pname and getattr(p, "__class__", None).__name__ == "ToolReturnPart":
                responses.append(pname)

    print("\n--- Tool Requests (assistant -> tool) ---")
    if requests:
        for tool_name in requests:
            print(f"- {tool_name}")
    else:
        print("(none)")

    print("\n--- Tool Responses (tool -> assistant) ---")
    if responses:
        for tool_name in responses:
            print(f"- {tool_name}")
    else:
        print("(none)")


def stream_answer(rag_agent, query: str, request_limit: Optional[int]):
    """Stream the agent's structured response for the provided query."""
    streamed_chunks: List[str] = []
    final_result = None
    run_id = str(uuid.uuid4())

    class AnswerHandler(JSONParserHandler):
        """Stream the `answer` field out of the JSON tool call as it arrives."""

        def on_value_chunk(self, path, field_name, chunk):
            if path == "" and field_name == "answer":
                print(chunk, end="", flush=True)
                streamed_chunks.append(chunk)

    parser = StreamingJSONParser(AnswerHandler())

    def handle_chunk(chunk: str):
        if chunk is None or chunk == "":
            return
        try:
            parser.parse_incremental(chunk)
        except Exception:
            # If parsing fails (e.g., provider returned plain text), fallback to direct print
            print(chunk, end="", flush=True)
            streamed_chunks.append(chunk)

    async def run_and_stream():
        nonlocal final_result
        async for event in rag_agent.run_stream_events(
            query,
            usage_limits=ai_usage.UsageLimits(request_limit=request_limit),
            usage=ai_usage.RunUsage(),
        ):
            if isinstance(event, ai_messages.PartStartEvent):
                part = getattr(event, "part", None)
                kind = getattr(part, "part_kind", None)
                if kind == "text":
                    handle_chunk(getattr(part, "content", "") or "")
                elif kind == "tool_call":
                    args = getattr(part, "args", "")
                    if isinstance(args, str):
                        handle_chunk(args)
                log_event(
                    {"event": "part_start", "kind": kind, "query": query},
                    run_id=run_id,
                )
            elif isinstance(event, ai_messages.PartDeltaEvent):
                delta_obj = event.delta
                if getattr(delta_obj, "part_delta_kind", None) == "text":
                    handle_chunk(getattr(delta_obj, "content_delta", None))
                elif getattr(delta_obj, "part_delta_kind", None) == "tool_call":
                    args_delta = getattr(delta_obj, "args_delta", None)
                    if isinstance(args_delta, str):
                        handle_chunk(args_delta)
                log_event(
                    {"event": "part_delta", "kind": getattr(delta_obj, "part_delta_kind", None), "query": query},
                    run_id=run_id,
                )
            elif isinstance(event, ai_messages.PartEndEvent):
                part = getattr(event, "part", None)
                kind = getattr(part, "part_kind", None)
                if kind == "text":
                    # Ensure newline separation after text parts end
                    print("", end="", flush=True)
                log_event({"event": "part_end", "kind": kind, "query": query}, run_id=run_id)
            elif isinstance(event, AgentRunResultEvent):
                final_result = event.result
                usage_obj = getattr(event.result, "_state", None)
                usage_obj = getattr(usage_obj, "usage", None) if usage_obj else None
                log_event(
                    {
                        "event": "final_result",
                        "query": query,
                        "answer": getattr(event.result.output, "answer", None),
                        "references": getattr(event.result.output, "references", None),
                        "usage": {
                            "requests": getattr(usage_obj, "requests", None),
                            "input_tokens": getattr(usage_obj, "input_tokens", None),
                            "output_tokens": getattr(usage_obj, "output_tokens", None),
                        },
                    },
                    run_id=run_id,
                )

    print("\nAssistant:\n")
    asyncio.run(run_and_stream())

    if final_result is None:
        raise RuntimeError("Stream ended without a final result.")

    final_output = final_result.output

    if not streamed_chunks and final_output.answer:
        print(final_output.answer)

    if final_output.references:
        print("\n\nReferences:")
        for ref in final_output.references:
            print(f"- {ref}")

    return final_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream responses from the Macaulay2 RAG agent.")
    parser.add_argument(
        "query",
        nargs="?",
        default="how do you define a monomial ideal in macaulay 2?",
        help="Prompt to send to the agent.",
    )
    parser.add_argument(
        "--request-limit",
        type=int,
        default=50,
        help="Max model requests per run before failing (set to 0 or negative to disable).",
    )
    parser.add_argument(
        "--index-mode",
        choices=["docs", "chunks"],
        help="Index mode to use (overrides M2_INDEX_MODE).",
    )
    args = parser.parse_args()

    if args.index_mode:
        os.environ["M2_INDEX_MODE"] = args.index_mode
    else:
        os.environ.setdefault("M2_INDEX_MODE", "chunks")
    from src.agents.rag_agent import rag_agent

    print(f"Query: {args.query}")
    request_limit = None if args.request_limit and args.request_limit <= 0 else args.request_limit
    stream_result = stream_answer(rag_agent, args.query, request_limit)
    print_tool_calls(stream_result)

    # Print usage to help diagnose request-limit issues.
    usage_obj = getattr(stream_result, "_state", None)
    usage_obj = getattr(usage_obj, "usage", None) if usage_obj else None
    if usage_obj:
        print(
            "\nUsage summary:"
            f" requests={usage_obj.requests}, tool_calls={usage_obj.tool_calls}, "
            f"input_tokens={usage_obj.input_tokens}, output_tokens={usage_obj.output_tokens}"
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
