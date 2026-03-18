"""
run.py
Main entry point for the Autonomous Cognitive Engine.

Usage:
    python run.py
"""

from __future__ import annotations
import json
import sys

from langchain_core.messages import HumanMessage

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from tools import _set_files
from graph import graph

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


def run_agent(user_input: str) -> dict:
    _set_files({})

    print(f"\n  Task : {user_input}\n")

    final_state  = {}
    plan_printed = False

    for chunk in graph.stream(
        {
            "messages": [HumanMessage(content=user_input)],
            "todos":    [],
            "current_task_index": None,
            "files":    {},
            "execution_log": [],
        },
        stream_mode="updates",
    ):
        for node_name, state_delta in chunk.items():

            todos = state_delta.get("todos", [])
            log   = state_delta.get("execution_log", [])

            # ── MILESTONE 1: print JSON plan (all pending) on first creation ─
            if node_name == "process" and todos and not plan_printed:
                plan_printed = True

                print(SEP)
                print(" TASK PLAN CREATED")
                print(SEP)
                plan_json = [
                    {"task": t["task"], "status": t["status"], "result": t.get("result", "")}
                    for t in todos
                ]
                print(json.dumps(plan_json, indent=2))
                print()

            # ── Live progress ─────────────────────────────────────────────
            if log:
                latest = log[-1]

                # ⏳ task starting
                if node_name == "select_task" and "[Select] Task" in latest:
                    try:
                        part = latest.split("[Select] Task ")[1]
                        num_part, name_part = part.split(": ", 1)
                        x, n = num_part.split("/")
                        print(f"⏳ Executing Task {x}/{n}: {name_part}")
                    except Exception:
                        pass

                # ✅ task completed
                if node_name == "update_task" and "[Update] Task" in latest and "marked completed" in latest:
                    try:
                        part = latest.split("[Update] Task ")[1]
                        num_part = part.split(" marked")[0]
                        x, n = num_part.split("/")
                        print(f"✅ Completed Task {x}/{n}")
                    except Exception:
                        pass

                # 🔀 delegation
                if "[Milestone3]" in latest:
                    agent = latest.split("sub-agent: ")[-1]
                    print(f"  🔀 Delegated → {agent}")

            # final report done
            if node_name == "synthesize":
                print(f"\n✅ Final report created")

            # merge state
            for k, v in state_delta.items():
                if isinstance(v, list) and k in ("todos", "execution_log"):
                    final_state[k] = v
                elif isinstance(v, dict) and k == "files":
                    final_state.setdefault("files", {}).update(v)
                else:
                    final_state[k] = v

    # ── Final display ──────────────────────────────────────────────────────
    todos = final_state.get("todos", [])
    files = final_state.get("files", {})
    log   = final_state.get("execution_log", [])

    _display_results(todos, files, log)
    return final_state


def _display_results(todos: list, files: dict, log: list) -> None:

    # ── Print updated JSON with all tasks completed ───────────────────────
    print()
    print(SEP)
    print(" TASK PLAN COMPLETED")
    print(SEP)
    plan_json = [
        {"task": t["task"], "status": t.get("status", "completed"), "result": t.get("result", "")}
        for t in todos
    ]
    print(json.dumps(plan_json, indent=2))
    print()

    # ── MILESTONE 2 ───────────────────────────────────────────────────────
    print(SEP)
    print(f" MILESTONE 2  —  Virtual File System  ({len(files)} files)")
    print(SEP)
    if files:
        for fname in sorted(files.keys()):
            print(f"  - {fname:<44} ({len(files[fname])} chars)")
    else:
        print("  No files created.")

    # Show edit_file usage from log
    edit_logs = [l for l in log if "edit_file" in l.lower() or "[Execute] Tools called:" in l and "edit_file" in l]
    edits = [l for l in log if "[Execute] Tools called:" in l and "edit_file" in l]
    if edits:
        print(f"\n  ✏️  edit_file used: {len(edits)} time(s)  — read→modify→edit chain demonstrated")

    # ── MILESTONE 3 ───────────────────────────────────────────────────────
    delegations = [l for l in log if "[Milestone3]" in l]
    print()
    print(SEP)
    print(f" MILESTONE 3  —  Sub-Agent Delegations ")
    print(SEP)
    if delegations:
        for entry in delegations:
            agent = entry.split("sub-agent: ")[-1]
            print(f"  🔀 {agent}")
    else:
        print("  No delegations this run.")

    # ── FINAL REPORT ──────────────────────────────────────────────────────
    print()
    print(SEP)
    print(" FINAL REPORT")
    print(SEP)
    if "FINAL_REPORT.txt" in files:
        print(files["FINAL_REPORT.txt"])
    else:
        print("  No final report generated.")

    print(SEP)


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
    