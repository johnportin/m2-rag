"""Utility script to verify that the agent wiring records tool calls.

This uses `pydantic_ai.models.TestModel`, which deterministically invokes the
registered tools instead of reaching out to OpenAI. Running the script prints
the agent's response plus the tool request/response objects captured in the
result, so you can confirm the plumbing works end-to-end without network calls.
"""

import os
from pathlib import Path
import sys

from pydantic_ai.models.test import TestModel

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure rag_agent can be imported without a real OpenAI key
os.environ.setdefault("OPENAI_API_KEY", "test")

from src.agents.rag_agent import rag_agent
from src.main import print_tool_calls


def run_test_agent() -> None:
    """Run the RAG agent with the deterministic TestModel and log tool calls."""
    # `call_tools='all'` forces the model stub to invoke every registered tool
    # (search_docs first, then summarize_docs). `custom_output_args` returns a
    # structure compatible with the agent's output schema.
    test_model = TestModel(
        call_tools="all",
        custom_output_args={"answer": "(test complete)", "references": ["[test_source] synthetic reference"]},
    )
    with rag_agent.override(model=test_model):
        result = rag_agent.run_sync("debug tool usage")

    agent_output = getattr(result, "output", None)
    response_text = getattr(agent_output, "answer", "")
    references = getattr(agent_output, "references", [])

    print("\n=== Test Agent Response ===")
    print(response_text or "<empty response>")
    if references:
        print("\nReferences:")
        for ref in references:
            print(f"- {ref}")

    print("\n=== Recorded Tool Calls ===")
    print_tool_calls(result)


if __name__ == "__main__":
    run_test_agent()
