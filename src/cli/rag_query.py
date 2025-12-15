from __future__ import annotations

import argparse
import os


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RAG agent against a query.")
    parser.add_argument(
        "--query",
        "-q",
        required=False,
        help="Query to ask the agent (default is a sample question).",
    )
    parser.add_argument(
        "--index-mode",
        choices=["docs", "chunks"],
        default="chunks",
        help="Index mode to use (default: chunks).",
    )
    return parser.parse_args()


def main() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # If dotenv isn't available for some reason, continue; env may already be set.
        pass

    # Silence tokenizers fork warning from huggingface.
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    args = parse_args()
    query = args.query or "how do you define a monomial ideal in macaulay 2?"

    # Set index mode for this run
    os.environ["M2_INDEX_MODE"] = args.index_mode

    # Import after environment is loaded so API keys are available.
    from src.agents.rag_agent import rag_agent

    result = rag_agent.run_sync(query)
    print(result.output.answer)
    if result.output.references:
        print("\nReferences:")
        for ref in result.output.references:
            print(f"- {ref}")

    rag_messages = result.all_messages() if callable(getattr(result, "all_messages", None)) else result.all_messages
    print("\n--- Used sources ---")
    for m in rag_messages:
        if getattr(m, "tool_name", None) == "search_docs":
            args = getattr(m, "args", None) or getattr(m, "tool_args", None)
            print(f"search_docs: {args}")


if __name__ == "__main__":
    main()
