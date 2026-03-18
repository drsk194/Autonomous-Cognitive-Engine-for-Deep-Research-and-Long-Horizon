"""
eval.py
Milestone evaluation script — Milestones 1, 2, and 3.

Runs 7 test prompts and scores each against milestone criteria.
Prints a detailed report and final pass/fail per milestone.

Usage:
    python eval.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import List

from langchain_core.messages import HumanMessage

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from tools import _set_files
from graph import graph

# ===========================================================================
# Test prompts — 7 complex inputs covering all milestones
# ===========================================================================

TEST_CASES = [
    # M1 focus — planning quality
    "Generate a comprehensive research report on the impact of artificial intelligence in healthcare",

    "Create a detailed business plan for an AI-powered smart agriculture startup in India",

    # M2 focus — file system usage
    "Analyze four AI ethics frameworks, identify differences, and propose a unified model",

    "Refactor a legacy monolithic Python application into microservices using clean architecture",

    # M3 focus — delegation with Tavily
    "Analyze the current state of generative AI startups in 2025, identify top players and their funding",

    "Research the latest developments in quantum computing in 2025 and analyze its impact on cybersecurity",

    # End-to-end
    "Perform a competitive analysis of electric vehicle companies in India including market share and battery technology",
]


# ===========================================================================
# Evaluation result dataclass
# ===========================================================================

@dataclass
class EvalResult:
    prompt:        str
    # M1
    m1_pass:       bool  = False
    todo_count:    int   = 0
    todos_completed: int = 0
    action_verbs:  bool  = False
    # M2
    m2_pass:       bool  = False
    files_created: int   = 0
    result_files:  int   = 0
    edit_used:     bool  = False
    avg_file_size: int   = 0
    # M3
    m3_pass:       bool  = False
    delegations:   int   = 0
    agents_used:   List[str] = field(default_factory=list)
    tavily_used:   bool  = False
    # General
    has_final_report: bool = False
    error:         str  = ""


ACTION_VERBS = [
    "analyze", "research", "identify", "design", "write", "compare",
    "evaluate", "develop", "create", "build", "gather", "summarize",
    "review", "propose", "implement", "assess", "examine",
]


def evaluate(state: dict, prompt: str) -> EvalResult:
    r = EvalResult(prompt=prompt)
    todos  = state.get("todos", [])
    files  = state.get("files", {})
    log    = state.get("execution_log", [])

    # ── Milestone 1 ───────────────────────────────────────────────────────
    r.todo_count      = len(todos)
    r.todos_completed = sum(1 for t in todos if t.get("status") == "completed")
    r.action_verbs    = all(
        any(t["task"].lower().startswith(v) for v in ACTION_VERBS)
        for t in todos
    )
    r.m1_pass = (
        4 <= r.todo_count <= 6
        and r.todos_completed == r.todo_count
        and r.action_verbs
    )

    # ── Milestone 2 ───────────────────────────────────────────────────────
    r.files_created = len(files)
    r.result_files  = sum(1 for f in files if "result" in f)
    r.edit_used     = any("[Execute] Tools called:" in l and "edit_file" in l for l in log)
    r.has_final_report = "FINAL_REPORT.txt" in files

    # Check avg result file size — should be > 100 chars (not just a label)
    result_sizes = [len(v) for k, v in files.items() if "result" in k]
    r.avg_file_size = int(sum(result_sizes) / len(result_sizes)) if result_sizes else 0

    r.m2_pass = (
        r.result_files >= 3
        and r.has_final_report
        and r.avg_file_size > 100      # actual content, not just labels
    )

    # ── Milestone 3 ───────────────────────────────────────────────────────
    delegation_logs  = [l for l in log if "[Milestone3]" in l]
    r.delegations    = len(delegation_logs)
    r.agents_used    = list({l.split("sub-agent: ")[-1] for l in delegation_logs})
    r.tavily_used    = any("[Tavily]" in l for l in log) or any(
        "researcher" in l or "analyst" in l for l in delegation_logs
    )
    r.m3_pass = r.delegations >= 1 and len(r.agents_used) >= 1

    return r


# ===========================================================================
# Scoring helpers
# ===========================================================================

def score_result(r: EvalResult) -> dict:
    """Assign 1-5 points per dimension (as per task requirements)."""
    scores = {}

    # M1 dimensions
    scores["todo_structure"]   = 5 if (4 <= r.todo_count <= 6 and r.action_verbs) else (3 if 4 <= r.todo_count <= 6 else 1)
    scores["todo_completion"]  = 5 if r.todos_completed == r.todo_count else int(r.todos_completed / max(r.todo_count, 1) * 5)
    scores["json_output"]      = 5 if r.todo_count > 0 else 1

    # M2 dimensions
    scores["file_usage"]       = 5 if r.result_files >= 4 else (3 if r.result_files >= 2 else 1)
    scores["file_content"]     = 5 if r.avg_file_size > 500 else (3 if r.avg_file_size > 100 else 1)
    scores["edit_file"]        = 5 if r.edit_used else 2
    scores["final_report"]     = 5 if r.has_final_report else 1

    # M3 dimensions
    scores["delegation_count"] = 5 if r.delegations >= 3 else (3 if r.delegations >= 1 else 1)
    scores["correct_agents"]   = 5 if len(r.agents_used) >= 2 else (3 if len(r.agents_used) == 1 else 1)
    scores["tavily_search"]    = 5 if r.tavily_used else 2

    return scores


def fmt_pass(b: bool) -> str:
    return "PASS ✓" if b else "FAIL ✗"


# ===========================================================================
# Main evaluation runner
# ===========================================================================

def run_evaluation(cases: List[str] | None = None) -> None:
    cases = cases or TEST_CASES
    results: List[EvalResult] = []

    print("\n" + "=" * 66)
    print("  MILESTONE EVALUATION — Deep Research Agent")
    print("  M1: Planning  |  M2: File System  |  M3: Delegation + Tavily")
    print("=" * 66)

    for i, prompt in enumerate(cases, 1):
        print(f"\n{'─' * 66}")
        print(f"Test {i}/{len(cases)}")
        print(f"Prompt: {prompt[:75]}{'...' if len(prompt) > 75 else ''}")
        print("─" * 66)

        _set_files({})

        try:
            state = graph.invoke({
                "messages": [HumanMessage(content=prompt)],
                "todos":    [],
                "current_task_index": None,
                "files":    {},
                "execution_log": [],
            })
            r = evaluate(state, prompt)

        except Exception as exc:
            r = EvalResult(prompt=prompt, error=str(exc)[:200])
            print(f"  ERROR: {exc}")

        results.append(r)
        scores = score_result(r)

        # Per-test output
        print(f"\n  MILESTONE 1  [{fmt_pass(r.m1_pass)}]")
        print(f"    TODOs generated  : {r.todo_count}  (need 4-6)")
        print(f"    TODOs completed  : {r.todos_completed}/{r.todo_count}")
        print(f"    Action verbs     : {'Yes' if r.action_verbs else 'No'}")
        print(f"    Score            : {scores['todo_structure']}/5  (structure)  "
              f"{scores['todo_completion']}/5  (completion)  "
              f"{scores['json_output']}/5  (JSON output)")

        print(f"\n  MILESTONE 2  [{fmt_pass(r.m2_pass)}]")
        print(f"    Files created    : {r.files_created}")
        print(f"    Result files     : {r.result_files}")
        print(f"    Avg result size  : {r.avg_file_size} chars")
        print(f"    edit_file used   : {'Yes' if r.edit_used else 'No'}")
        print(f"    Final report     : {'Yes' if r.has_final_report else 'No'}")
        print(f"    Score            : {scores['file_usage']}/5  (file usage)  "
              f"{scores['file_content']}/5  (content size)  "
              f"{scores['edit_file']}/5  (edit_file)  "
              f"{scores['final_report']}/5  (final report)")

        print(f"\n  MILESTONE 3  [{fmt_pass(r.m3_pass)}]")
        print(f"    Delegations      : {r.delegations}")
        print(f"    Agents used      : {r.agents_used or 'none'}")
        print(f"    Tavily search    : {'Yes' if r.tavily_used else 'No'}")
        print(f"    Score            : {scores['delegation_count']}/5  (delegation count)  "
              f"{scores['correct_agents']}/5  (agent selection)  "
              f"{scores['tavily_search']}/5  (Tavily usage)")

        if r.error:
            print(f"\n  Error: {r.error}")

        time.sleep(1)

    # ── Aggregate summary ──────────────────────────────────────────────────
    total   = len(results)
    m1_pass = sum(1 for r in results if r.m1_pass)
    m2_pass = sum(1 for r in results if r.m2_pass)
    m3_pass = sum(1 for r in results if r.m3_pass)

    all_scores = [score_result(r) for r in results]

    def avg_score(key):
        return round(sum(s[key] for s in all_scores) / total, 1)

    print("\n" + "=" * 66)
    print("  FINAL EVALUATION SUMMARY")
    print("=" * 66)
    print(f"  Total test cases     : {total}")
    print()
    print(f"  Milestone 1  Pass    : {m1_pass}/{total}  ({m1_pass/total*100:.0f}%)")
    print(f"    Avg todo structure : {avg_score('todo_structure')}/5")
    print(f"    Avg completion     : {avg_score('todo_completion')}/5")
    print(f"    Avg JSON output    : {avg_score('json_output')}/5")
    print()
    print(f"  Milestone 2  Pass    : {m2_pass}/{total}  ({m2_pass/total*100:.0f}%)")
    print(f"    Avg file usage     : {avg_score('file_usage')}/5")
    print(f"    Avg content size   : {avg_score('file_content')}/5")
    print(f"    Avg edit_file      : {avg_score('edit_file')}/5")
    print(f"    Avg final report   : {avg_score('final_report')}/5")
    print()
    print(f"  Milestone 3  Pass    : {m3_pass}/{total}  ({m3_pass/total*100:.0f}%)")
    print(f"    Avg delegation     : {avg_score('delegation_count')}/5")
    print(f"    Avg agent select   : {avg_score('correct_agents')}/5")
    print(f"    Avg Tavily usage   : {avg_score('tavily_search')}/5")
    print()

    threshold = 0.80
    print("  Pass/fail vs 80% threshold:")
    for label, passed in [
        ("Milestone 1 — Planning",       m1_pass / total),
        ("Milestone 2 — File System",    m2_pass / total),
        ("Milestone 3 — Delegation",     m3_pass / total),
    ]:
        status = "PASS ✓" if passed >= threshold else "FAIL ✗"
        print(f"    {label:30s} {status}  ({passed*100:.0f}%  vs  {threshold*100:.0f}% needed)")

    print("=" * 66 + "\n")


if __name__ == "__main__":
    run_evaluation()
    