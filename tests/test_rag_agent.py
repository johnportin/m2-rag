from __future__ import annotations

from pydantic_ai.messages import ToolCallPart, ToolReturnPart


def _extract_tool_parts(result):
    tool_calls = []
    tool_returns = []
    for message in result.all_messages():
        for part in getattr(message, "parts", []) or []:
            if isinstance(part, ToolCallPart):
                tool_calls.append(part)
            elif isinstance(part, ToolReturnPart):
                tool_returns.append(part)
    return tool_calls, tool_returns


def test_agent_invokes_tools(test_rag_agent):
    result = test_rag_agent.run_sync("debug tool usage")

    tool_calls, tool_returns = _extract_tool_parts(result)

    call_names = [call.tool_name for call in tool_calls]
    return_names = [ret.tool_name for ret in tool_returns]

    # `TestModel(call_tools='all')` should force both registered tools to run
    assert "search_docs" in call_names, "search_docs tool was not called"
    assert "summarize_docs" in call_names, "summarize_docs tool was not called"
    assert "search_docs" in return_names, "search_docs tool did not return data"
    assert "summarize_docs" in return_names, "summarize_docs tool did not return data"

    assert result.output.answer == "(test complete)"
    assert result.output.references
