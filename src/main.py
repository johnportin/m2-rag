from __future__ import annotations

import argparse
import sys
from typing import List

from pydantic_ai import messages as ai_messages

from src.agents.rag_agent import rag_agent


def print_tool_calls(result) -> None:
    """Pretty-print tool call activity recorded during the run."""
    msgs = result.all_messages() if callable(getattr(result, "all_messages", None)) else result.all_messages

    print("\n--- Tool Requests (assistant -> tool) ---")
    any_req = False
    for m in msgs:
        role = getattr(m, "role", None)
        tool_name = getattr(m, "tool_name", None) or getattr(m, "name", None)
        if tool_name and role in (None, "assistant", "assistant_tool_call"):
            any_req = True
            args = getattr(m, "args", None) or getattr(m, "tool_args", None)
            print(f"- {tool_name}")
            if args is not None:
                try:
                    print(f"  args: {args.model_dump()}")
                except Exception:
                    print(f"  args: {args}")
    if not any_req:
        print("(none)")

    print("\n--- Tool Responses (tool -> assistant) ---")
    any_resp = False
    for m in msgs:
        if getattr(m, "role", None) == "tool":
            any_resp = True
            tname = getattr(m, "tool_name", None) or getattr(m, "name", None) or "<unknown>"
            content = getattr(m, "content", None)
            print(f"- {tname}")
            if content is not None:
                print(f"  result: {content}")
    if not any_resp:
        print("(none)")


def stream_answer(query: str):
    """Stream the agent's structured response for the provided query."""
    streamed_chunks: List[str] = []

    async def event_stream_handler(_, events):
        async for event in events:
            if isinstance(event, ai_messages.PartDeltaEvent):
                delta = event.delta
                content = getattr(delta, "content_delta", None)
                if content:
                    print(content, end="", flush=True)
                    streamed_chunks.append(content)
            elif isinstance(event, ai_messages.PartEndEvent):
                if getattr(event.part, "part_kind", None) == "text":
                    print("", end="", flush=True)

    print("\nAssistant:\n")
    result = rag_agent.run_sync(query, event_stream_handler=event_stream_handler)
    final_output = result.output

    if not streamed_chunks and final_output.answer:
        print(final_output.answer)

    if final_output.references:
        print("\n\nReferences:")
        for ref in final_output.references:
            print(f"- {ref}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream responses from the Macaulay2 RAG agent.")
    parser.add_argument(
        "query",
        nargs="?",
        default="how do you define a monomial ideal in macaulay 2?",
        help="Prompt to send to the agent.",
    )
    args = parser.parse_args()

    print(f"Query: {args.query}")
    stream_result = stream_answer(args.query)
    print_tool_calls(stream_result)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
