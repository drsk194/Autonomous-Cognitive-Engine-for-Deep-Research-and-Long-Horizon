"""
run.py — Main entry point for the Autonomous Cognitive Engine.
Usage: python run.py
"""
from __future__ import annotations
import json, os, sys

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

from tools import _set_files
from graph import graph
from memory import search_memory

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║         AUTONOMOUS COGNITIVE ENGINE  —  Deep Research Agent      ║
╠══════════════════════════════════════════════════════════════════╣
║  Milestone 1 : Structured Planning   (write_todos)               ║
║  Milestone 2 : Virtual File System   (write / read / edit)       ║
║  Milestone 3 : Sub-Agent Delegation  (summarizer / analyst / ..) ║
╚══════════════════════════════════════════════════════════════════╝
"""

SEP = "=" * 50

# ── Simple query classifier + direct answerer ─────────────────────────────────
_llm_chat = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    api_key=os.getenv("GROQ_API_KEY", ""),
    max_tokens=512,
)

_SIMPLE_KEYWORDS = {
    "what is", "what are", "what does", "what do", "what was",
    "who is", "who are", "who was",
    "how does", "how do", "how is",
    "why is", "why are", "why does",
    "define ", "explain ", "meaning of", "tell me about",
    "difference between", "example of", "examples of",
    "when was", "when did", "where is", "where are",
}

def _is_simple_query(text: str) -> bool:
    """Return True if the input looks like a simple factual/conversational question."""
    t = text.lower().strip()
    # Short inputs are likely simple
    if len(t.split()) <= 6:
        return True
    # Starts with a known simple pattern
    if any(t.startswith(kw) for kw in _SIMPLE_KEYWORDS):
        return True
    # Ends with a question mark and is short-ish
    if t.endswith("?") and len(t.split()) <= 12:
        return True
    return False


def _direct_answer(query: str) -> str:
    """Answer a simple question directly without the full pipeline."""
    response = _llm_chat.invoke([
        SystemMessage(content=(
            "You are a helpful, knowledgeable assistant. "
            "Answer the user's question clearly and concisely. "
            "No need for structured reports or plans — just a direct, friendly answer."
        )),
        HumanMessage(content=query),
    ])
    return response.content.strip()


def run_agent(user_input: str) -> dict:
    # ── Simple query — answer directly, skip the full pipeline ───────────
    if _is_simple_query(user_input):
        print(f"\n💬 Simple query detected — answering directly\n")
        answer = _direct_answer(user_input)
        print(answer)
        return {"files": {"DIRECT_ANSWER.txt": answer}, "simple": True}

    # ── Memory cache check — skip LLM if report already exists ───────────
    cached = search_memory(user_input)
    if cached:
        best = max(cached, key=lambda x: len(x.get("summary", "")))
        print(f"\n⚡ Found in memory — skipping LLM execution\n")

        todos = best.get("todos", [])
        if todos:
            print(SEP)
            print(" TASK PLAN (FROM MEMORY)")
            print(SEP)
            print(json.dumps(
                [{"task": t["task"], "status": t.get("status","completed"), "result": t.get("result","")} for t in todos],
                indent=2
            ))
            print()

        print(SEP)
        print(" FINAL REPORT (FROM MEMORY)")
        print(SEP)
        print(best["summary"])
        print(SEP)
        return {"files": {"FINAL_REPORT.txt": best["summary"]}}

    # ── Fresh execution ───────────────────────────────────────────────────
    _set_files({})
    print(f"\n  Task : {user_input}\n")

    final_state  = {}
    plan_printed = False

    for chunk in graph.stream(
        {
            "messages":           [HumanMessage(content=user_input)],
            "todos":              [],
            "current_task_index": None,
            "files":              {},
            "execution_log":      [],
            "delegation_log":     [],
            "final_report":       None,
        },
        stream_mode="updates",
    ):
        for node_name, state_delta in chunk.items():
            todos = state_delta.get("todos", [])
            log   = state_delta.get("execution_log", [])

            # Milestone 1 — print plan on first creation
            if node_name == "process" and todos and not plan_printed:
                plan_printed = True
                print(SEP)
                print(" TASK PLAN CREATED")
                print(SEP)
                print(json.dumps(
                    [{"task": t["task"], "status": t["status"], "result": t.get("result","")} for t in todos],
                    indent=2
                ))
                print()

            # Live progress
            if log:
                latest = log[-1]

                if node_name == "select_task" and "[Select] Task" in latest:
                    try:
                        part = latest.split("[Select] Task ")[1]
                        num_part, name_part = part.split(": ", 1)
                        x, n = num_part.split("/")
                        print(f"⏳ Executing Task {x}/{n}: {name_part}")
                    except Exception:
                        pass

                if node_name == "update_task" and "[Update] Task" in latest and "marked completed" in latest:
                    try:
                        part = latest.split("[Update] Task ")[1]
                        x, n = part.split(" marked")[0].split("/")
                        print(f"✅ Completed Task {x}/{n}")
                    except Exception:
                        pass

                if "[Milestone3]" in latest:
                    agent = latest.split("sub-agent: ")[-1]
                    print(f"  🔀 Delegated → {agent}")

            if node_name == "synthesize":
                print(f"\n✅ Final report created")

            # Merge state
            for k, v in state_delta.items():
                if isinstance(v, list) and k in ("todos", "execution_log", "delegation_log"):
                    final_state[k] = v
                elif isinstance(v, dict) and k == "files":
                    final_state.setdefault("files", {}).update(v)
                else:
                    final_state[k] = v

    _display_results(
        final_state.get("todos", []),
        final_state.get("files", {}),
        final_state.get("execution_log", []),
        final_state.get("delegation_log", []),
    )
    return final_state


def _display_results(todos: list, files: dict, log: list, delegation_log: list = None) -> None:
    print()
    print(SEP)
    print(" TASK PLAN COMPLETED")
    print(SEP)
    print(json.dumps(
        [{"task": t["task"], "status": t.get("status","completed"), "result": t.get("result","")} for t in todos],
        indent=2
    ))
    print()

    # Milestone 2 — virtual file system
    print(SEP)
    print(f" MILESTONE 2  —  Virtual File System  ({len(files)} files)")
    print(SEP)
    if files:
        for fname in sorted(files.keys()):
            print(f"  - {fname:<44} ({len(files[fname])} chars)")
    else:
        print("  No files created.")

    edits = [l for l in log if "[Execute] Tools called:" in l and "edit_file" in l]
    if edits:
        print(f"\n  ✏️  edit_file used: {len(edits)} time(s)  — read→modify→edit chain demonstrated")

    # Milestone 3 — delegations
    delegations = [l for l in log if "[Milestone3]" in l]
    print()
    print(SEP)
    print(" MILESTONE 3  —  Sub-Agent Delegations")
    print(SEP)
    if delegations:
        for entry in delegations:
            agent = entry.split("sub-agent: ")[-1]
            print(f"  🔀 {agent}")
    else:
        print("  No delegations this run.")

    # Milestone 4 — delegation log
    if delegation_log:
        print()
        print(SEP)
        print(" MILESTONE 4  —  Delegation Log")
        print(SEP)
        for entry in delegation_log:
            print(f"  📋 {entry}")

    # Final report
    print()
    print(SEP)
    print(" FINAL REPORT")
    print(SEP)
    if "FINAL_REPORT.txt" in files:
        print(files["FINAL_REPORT.txt"])
    else:
        print("  No final report generated.")
    print(SEP)


def run_supervisor(query: str) -> tuple[str, bool]:
    """Run the agent and return (report_string, is_simple). Used by FastAPI."""
    result = run_agent(query)
    files = result.get("files", {})
    is_simple = result.get("simple", False)
    if is_simple:
        return files.get("DIRECT_ANSWER.txt", ""), True
    return files.get("FINAL_REPORT.txt", result.get("final_report", "No report generated.")), False


def main() -> None:
    print(BANNER)
    while True:
        print("\nEnter complex task:\n")
        try:
            user_input = input(">>> ").strip()
        except KeyboardInterrupt:
            print("\n\nExiting. Goodbye!")
            sys.exit(0)

        if not user_input:
            print("  ⚠️  Please enter a task.")
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            sys.exit(0)

        run_agent(user_input)


if __name__ == "__main__":
    main()
