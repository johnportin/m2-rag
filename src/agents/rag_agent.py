from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models.openai import OpenAIResponsesModel

from src.tools.search import get_last_search_results, search_docs
from src.tools.summarize import summarize_docs
from src.tools.wiki import search_wikipedia

# instructions = """
# You are a Macaulay2 documentation assistant.
# You **must** use the available tools to answer questions.

# Protocol:
# 1. Always call the `search_docs` tool first to find relevant documentation.
# 2. Use only the information returned by the tools when answering the user.
# 3. If no results are found, say you couldn't find relevant documentation.
# 4. Provide Macaulay2 code examples only if grounded in tool output.

# Do NOT rely on your own knowledge.
# Do NOT answer without using `search_docs` first.

# Cite each document using its source field.
# """
instructions = """
You are a Macaulay2 documentation assistant.
You **must** use the available tools to answer questions.

Protocol:
1) Always call `search_docs` first.
2) If `search_docs` returns results and k > 1, call `summarize_docs` to combine them.
3) If `search_docs` returns no results, call `search_wikipedia` using the key nouns from the user prompt.
4) Do not call `search_wikipedia` when `search_docs` already returned results.
5) When citing a Wikipedia result, include its full URL in the reference entry.
6) Answer only with tool-returned info; if nothing found, say so.
7) Provide Macaulay2 code examples only when grounded in tool output.

Final response format (always follow exactly):
Answer:
<write the final answer in complete sentences, optionally with Markdown lists/code>

References:
<if no references, write "None">
- [source] short note derived from tool output

Tool Trace:
<summarize which tools were called and why, one bullet per tool, or "None">

Cite each document using its source field in the References section only.
"""

class RagAgentResponse(BaseModel):
    answer: str = Field(..., description="Final answer shown to the user.")
    references: list[str] = Field(
        default_factory=list,
        description="List of cited documentation sources.",
    )


rag_agent = Agent(
    model=OpenAIResponsesModel("gpt-4o-mini"),
    tools=[search_docs, summarize_docs, search_wikipedia],
    instructions=instructions,
    output_type=RagAgentResponse,
)


@rag_agent.output_validator
def ensure_search_called(ctx: RunContext[None], data: RagAgentResponse) -> RagAgentResponse:
    """Ensure at least one search_docs tool call occurred before final answer."""
    for message in ctx.messages:
        parts = getattr(message, "parts", None) or []
        for part in parts:
            if isinstance(part, ToolCallPart) and part.tool_name == "search_docs":
                return data

    raise ModelRetry("You must call `search_docs` before responding.")


@rag_agent.output_validator
def ensure_references_present(_, data: RagAgentResponse) -> RagAgentResponse:
    """Ensure references are included when search results were found."""
    search_results = get_last_search_results()
    cleaned_refs: list[str] = []

    def normalize_ref(ref) -> str | None:
        if isinstance(ref, str):
            return ref if ref and ref.lower() != "none" else None
        if isinstance(ref, dict):
            src = ref.get("source") or ""
            url = ref.get("url") or ""
            # Prefer "source: url" if url present
            if src and url:
                return f"{src} ({url})"
            return src or url or None
        return None

    for ref in data.references:
        norm = normalize_ref(ref)
        if norm:
            cleaned_refs.append(norm)

    if search_results and not cleaned_refs:
        raise ModelRetry("You must include references sourced from the search results.")
    data.references = cleaned_refs
    return data


@rag_agent.output_validator
def ensure_wikipedia_urls(_, data: RagAgentResponse) -> RagAgentResponse:
    """Ensure any Wikipedia reference includes a URL."""
    updated_refs: list[str] = []
    for ref in data.references:
        if "wikipedia" in ref.lower() and "http" not in ref.lower():
            raise ModelRetry("Include the full Wikipedia URL in the reference entry.")
        updated_refs.append(ref)
    data.references = updated_refs
    return data
