from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models.openai import OpenAIResponsesModel

from src.tools.search import search_docs
from src.tools.summarize import summarize_docs

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
1. Always call the `search_docs` tool first to find relevant documentation.
2. If multiple search results are returned, call `summarize_docs` to combine and format them.
   Only call summarize_docs when search_docs returns results AND k > 1.
   Never call summarize_docs if search_docs returns an empty list.
3. Use only the information returned by the tools when answering the user.
4. If no results are found, say you couldn't find relevant documentation.
5. Provide Macaulay2 code examples only if grounded in tool output.

Do NOT rely on your own knowledge.
Do NOT answer without using `search_docs` first.

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
    tools=[search_docs, summarize_docs],
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

