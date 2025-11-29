from __future__ import annotations

from typing import Iterable, Sequence

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel


judge_instructions = """
You are an impartial evaluator for Macaulay2 documentation answers.

You will receive:
- Question: the original user query.
- Answer: the assistant's structured reply.
- References: list of strings like "[source] short note".
- Tool Summary: optional notes about which tools were invoked.

Evaluation rubric:
1. Accuracy: the answer must align with the cited Macaulay2 documentation.
2. Coverage: it should address every part of the question.
3. Grounding: every factual statement must be supported by the provided references.
4. References: the references list must contain at least one entry whenever documentation was available.

Produce an objective judgment without inventing information.
"""


class JudgeVerdict(BaseModel):
    decision: str = Field(
        ...,
        pattern="^(pass|fail)$",
        description='Overall decision for the answer, use "pass" for acceptable answers, "fail" otherwise.',
    )
    score: float = Field(..., ge=0.0, le=1.0, description="A score between 0 and 1 representing answer quality.")
    rationale: str = Field(..., description="Short narrative explaining the reasoning behind the score/decision.")
    required_improvements: list[str] = Field(
        default_factory=list,
        description="Actionable steps needed for the answer to pass (empty if already good).",
    )


def build_judge_prompt(
    question: str,
    answer: str,
    references: Sequence[str] | None = None,
    tool_notes: Sequence[str] | None = None,
) -> str:
    """Create a formatted prompt for the judge agent."""
    ref_block = "\n".join(f"- {ref}" for ref in (references or [])) or "(none)"
    tool_block = "\n".join(f"- {note}" for note in (tool_notes or [])) or "(not provided)"
    return (
        "Question:\n"
        f"{question}\n\n"
        "Answer:\n"
        f"{answer}\n\n"
        "References:\n"
        f"{ref_block}\n\n"
        "Tool Summary:\n"
        f"{tool_block}\n\n"
        "Provide your evaluation."
    )


judge_agent = Agent(
    model=OpenAIResponsesModel("gpt-4o-mini"),
    instructions=judge_instructions,
    output_type=JudgeVerdict,
)

