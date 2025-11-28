from __future__ import annotations

import argparse
import os
import re


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RAG agent against a query.")
    parser.add_argument(
        "--query",
        "-q",
        required=False,
        help="Query to ask the agent (default is a sample question).",
    )
    return parser.parse_args()


def simple_tokenize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return " ".join(tokens)


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
    processed_query = simple_tokenize(query)

    # Import after environment is loaded so API keys are available.
    from src.agents.rag_agent import rag_agent

    result = rag_agent.run_sync(processed_query)
    print(result.response.text)

    rag_messages = result.all_messages() if callable(getattr(result, "all_messages", None)) else result.all_messages
    print("\n--- Used sources ---")
    for m in rag_messages:
        if getattr(m, "tool_name", None) == "search_docs":
            args = getattr(m, "args", None) or getattr(m, "tool_args", None)
            print(f"search_docs: {args}")


if __name__ == "__main__":
    main()
