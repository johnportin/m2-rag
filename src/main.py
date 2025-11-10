from src.agents.rag_agent import rag_agent
import json

def print_tool_calls(result):
    # get messages whether all_messages is a method or attribute
    msgs = result.all_messages() if callable(getattr(result, "all_messages", None)) else result.all_messages

    print("\n--- Tool Requests (assistant → tool) ---")
    any_req = False
    for m in msgs:
        role = getattr(m, "role", None)
        tool_name = getattr(m, "tool_name", None) or getattr(m, "name", None)
        if tool_name and role in (None, "assistant", "assistant_tool_call"):
            any_req = True
            args = getattr(m, "args", None) or getattr(m, "tool_args", None)
            print(f"- {tool_name}")
            if args is not None:
                # keep it short/readable
                try:
                    print(f"  args: {args.model_dump()}")
                except Exception:
                    print(f"  args: {args}")
    if not any_req:
        print("(none)")

    print("\n--- Tool Responses (tool → assistant) ---")
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


if __name__=="__main__":
    print("Entered chatbot...")

    query = "how do you define a monomial ideal in macaulay 2?"

    result = rag_agent.run_sync(query)
    print(result.response.text)
    # for msg in result.all_messages():


    print_tool_calls(result)