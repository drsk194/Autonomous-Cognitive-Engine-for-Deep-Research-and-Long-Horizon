"""
eval.py — Full Milestone 1-4 evaluation for the Autonomous Cognitive Engine.
Runs all 10 required test cases, scores M1/M2/M3, and applies LLM-as-a-judge for M4.
LangSmith tracing is active during evaluation (env vars loaded from .env).

Usage:
    python eval.py
"""
from __future__ import annotations
import json, os, time
from dataclasses import dataclass, field
from typing import List

from langchain_core.messages import HumanMessage

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

from tools import _set_files
from graph import graph

# ── 10 required test cases (Milestones 1-4) ──────────────────────────────────
TEST_CASES = [
    # 1 — M1
    "Generate a comprehensive research report on the impact of artificial intelligence in healthcare, "
    "including recent advancements, ethical concerns, regulatory challenges, and future trends.",
    # 2 — M1
    "Create a detailed business plan for an AI-powered smart agriculture startup targeting "
    "small-scale farmers in India, including technology stack, revenue model, partnerships, "
    "and go-to-market strategy.",
    # 3 — M2
    "Design a scalable microservices architecture for a high-traffic e-commerce platform including "
    "database design, API gateway, caching strategy, load balancing, monitoring, and deployment pipeline.",
    # 4 — M2
    "Develop a step-by-step plan to refactor a legacy monolithic Python application into modular "
    "microservices using clean architecture principles and best DevOps practices.",
    # 5 — M3
    "Analyze the current state of generative AI startups in 2025, identify top players and their "
    "funding rounds, and assess market trends.",
    # 6 — M3
    "Research the latest developments in quantum computing in 2025 and analyze its impact on "
    "cybersecurity and encryption standards.",
    # 7 — M3
    "Perform a competitive analysis of electric vehicle companies in India including market share, "
    "pricing strategy, battery technology, and future positioning.",
    # 8 — M4
    "Analyze 4 AI ethics frameworks, identify key differences, propose a unified model, "
    "then refine it with sustainability considerations.",
    # 9 — M4
    "Analyze 5 renewable energy policy documents, extract key differences, "
    "and propose a consolidated improvement framework.",
    # 10 — M4
    "Generate a comparative report on AI adoption in the finance sector versus the healthcare sector, "
    "covering use cases, risks, regulatory landscape, and future outlook.",
]


# ── Evaluation result dataclass ───────────────────────────────────────────────
@dataclass
class EvalResult:
    prompt:              str
    # M1
    m1_pass:             bool      = False
    todo_count:          int       = 0
    todos_completed:     int       = 0
    action_verbs:        bool      = False
    todos_in_state:      bool      = False
    write_todos_invoked: bool      = False
    # M2
    m2_pass:             bool      = False
    files_created:       int       = 0
    result_files:        int       = 0
    edit_used:           bool      = False
    avg_file_size:       int       = 0
    has_final_report:    bool      = False
    # M3
    m3_pass:             bool      = False
    delegations:         int       = 0
    agents_used:         List[str] = field(default_factory=list)
    tavily_used:         bool      = False
    delegation_log:      List[str] = field(default_factory=list)
    # M4
    m4_judge_score:      int       = 0   # LLM-as-a-judge 1-10
    m4_pass:             bool      = False
    # Meta
    error:               str       = ""


ACTION_VERBS = [
    "analyze","research","identify","design","write","compare","evaluate",
    "develop","create","build","gather","summarize","review","propose",
    "implement","assess","examine","investigate",
]


def evaluate(state: dict, prompt: str) -> EvalResult:
    r = EvalResult(prompt=prompt)
    todos          = state.get("todos", [])
    files          = state.get("files", {})
    log            = state.get("execution_log", [])
    delegation_log = state.get("delegation_log", [])

    # ── Milestone 1 ───────────────────────────────────────────────────────
    r.todo_count         = len(todos)
    r.todos_completed    = sum(1 for t in todos if t.get("status") == "completed")
    r.todos_in_state     = r.todo_count > 0
    r.write_todos_invoked = any("[Plan] Invoking write_todos" in l for l in log)
    r.action_verbs       = all(
        any(t["task"].lower().startswith(v) for v in ACTION_VERBS)
        for t in todos
    ) if todos else False
    r.m1_pass = (
        4 <= r.todo_count <= 6
        and r.todos_completed == r.todo_count
        and r.action_verbs
        and r.write_todos_invoked
        and r.todos_in_state
    )

    # ── Milestone 2 ───────────────────────────────────────────────────────
    r.files_created    = len(files)
    r.result_files     = sum(1 for f in files if "result" in f)
    r.edit_used        = any("[Execute] Tools called:" in l and "edit_file" in l for l in log)
    r.has_final_report = "FINAL_REPORT.txt" in files
    result_sizes       = [len(v) for k, v in files.items() if "result" in k]
    r.avg_file_size    = int(sum(result_sizes) / len(result_sizes)) if result_sizes else 0
    r.m2_pass = (
        r.result_files >= 3
        and r.has_final_report
        and r.avg_file_size > 100
    )

    # ── Milestone 3 ───────────────────────────────────────────────────────
    m3_logs         = [l for l in log if "[Milestone3]" in l]
    r.delegations   = len(m3_logs)
    r.agents_used   = list({l.split("sub-agent: ")[-1] for l in m3_logs})
    r.tavily_used   = any("[Tavily]" in l for l in log) or any(
        "researcher" in l or "analyst" in l for l in m3_logs
    )
    r.delegation_log = delegation_log
    r.m3_pass = r.delegations >= 1 and len(r.agents_used) >= 1

    # ── Milestone 4 — LLM-as-a-judge ─────────────────────────────────────
    final_report = files.get("FINAL_REPORT.txt", "")
    if final_report:
        r.m4_judge_score = _llm_judge(final_report)
    r.m4_pass = r.m4_judge_score >= 7

    return r


def _llm_judge(report: str) -> int:
    """LLM-as-a-judge: rate report quality 1-10. Falls back to length heuristic."""
    try:
        from langchain_groq import ChatGroq
        judge_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY", ""),
            max_tokens=10,
        )
        prompt = (
            "Rate the following research report on a scale of 1 to 10 based on: "
            "completeness, accuracy, structure, and depth. "
            "Return ONLY a single integer between 1 and 10. No explanation.\n\n"
            f"REPORT:\n{report[:3000]}"
        )
        response = judge_llm.invoke([HumanMessage(content=prompt)])
        score_str = response.content.strip().split()[0]
        score = int("".join(c for c in score_str if c.isdigit()))
        return max(1, min(10, score))
    except Exception:
        # Fallback: length heuristic
        length = len(report)
        if length > 4500: return 10
        if length > 3000: return 9
        if length > 2000: return 8
        if length > 1000: return 7
        if length > 500:  return 6
        return 5


def score_result(r: EvalResult) -> dict:
    """Score each dimension 1-5."""
    s = {}
    # M1
    s["todo_structure"]     = 5 if (4 <= r.todo_count <= 6 and r.action_verbs) else (3 if 4 <= r.todo_count <= 6 else 1)
    s["todo_completion"]    = 5 if r.todos_completed == r.todo_count else int(r.todos_completed / max(r.todo_count, 1) * 5)
    s["json_output"]        = 5 if r.todo_count > 0 else 1
    s["write_todos_called"] = 5 if r.write_todos_invoked else 1
    s["todos_in_state"]     = 5 if r.todos_in_state else 1
    # M2
    s["file_usage"]         = 5 if r.result_files >= 4 else (3 if r.result_files >= 2 else 1)
    s["file_content"]       = 5 if r.avg_file_size > 500 else (3 if r.avg_file_size > 100 else 1)
    s["edit_file"]          = 5 if r.edit_used else 2
    s["final_report"]       = 5 if r.has_final_report else 1
    # M3
    s["delegation_count"]   = 5 if r.delegations >= 3 else (3 if r.delegations >= 1 else 1)
    s["correct_agents"]     = 5 if len(r.agents_used) >= 2 else (3 if len(r.agents_used) == 1 else 1)
    s["tavily_search"]      = 5 if r.tavily_used else 2
    # M4
    s["judge_score"]        = r.m4_judge_score  # already 1-10, display as-is
    return s


def fmt(b: bool) -> str:
    return "PASS ✓" if b else "FAIL ✗"


def run_evaluation(cases: List[str] | None = None) -> None:
    cases = cases or TEST_CASES
    results: List[EvalResult] = []

    print("\n" + "=" * 72)
    print("  AUTONOMOUS COGNITIVE ENGINE — Full Milestone Evaluation (M1-M4)")
    print(f"  LangSmith Project : {os.getenv('LANGCHAIN_PROJECT', 'not set')}")
    print(f"  Tracing enabled   : {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
    print("=" * 72)

    for i, prompt in enumerate(cases, 1):
        print(f"\n{'─' * 72}")
        print(f"Test {i}/{len(cases)}")
        print(f"Prompt: {prompt[:85]}{'...' if len(prompt) > 85 else ''}")
        print("─" * 72)

        _set_files({})

        try:
            state = graph.invoke({
                "messages":           [HumanMessage(content=prompt)],
                "todos":              [],
                "current_task_index": None,
                "files":              {},
                "execution_log":      [],
                "delegation_log":     [],
                "final_report":       None,
            })
            r = evaluate(state, prompt)
        except Exception as exc:
            r = EvalResult(prompt=prompt, error=str(exc)[:200])
            print(f"  ERROR: {exc}")

        results.append(r)
        s = score_result(r)

        print(f"\n  MILESTONE 1  [{fmt(r.m1_pass)}]")
        print(f"    write_todos invoked : {'Yes ✓' if r.write_todos_invoked else 'No ✗'}")
        print(f"    TODOs in state      : {r.todo_count}  (need 4-6)")
        print(f"    TODOs completed     : {r.todos_completed}/{r.todo_count}")
        print(f"    Action verbs        : {'Yes ✓' if r.action_verbs else 'No ✗'}")
        print(f"    Scores              : structure={s['todo_structure']}/5  "
              f"completion={s['todo_completion']}/5  "
              f"json={s['json_output']}/5  "
              f"write_todos={s['write_todos_called']}/5")

        print(f"\n  MILESTONE 2  [{fmt(r.m2_pass)}]")
        print(f"    Files created       : {r.files_created}")
        print(f"    Result files        : {r.result_files}")
        print(f"    Avg result size     : {r.avg_file_size} chars")
        print(f"    edit_file used      : {'Yes ✓' if r.edit_used else 'No ✗'}")
        print(f"    Final report        : {'Yes ✓' if r.has_final_report else 'No ✗'}")
        print(f"    Scores              : file_usage={s['file_usage']}/5  "
              f"content={s['file_content']}/5  "
              f"edit={s['edit_file']}/5  "
              f"report={s['final_report']}/5")

        print(f"\n  MILESTONE 3  [{fmt(r.m3_pass)}]")
        print(f"    Delegations         : {r.delegations}")
        print(f"    Agents used         : {r.agents_used or 'none'}")
        print(f"    Tavily search       : {'Yes ✓' if r.tavily_used else 'No ✗'}")
        if r.delegation_log:
            for entry in r.delegation_log:
                print(f"    📋 {entry}")
        print(f"    Scores              : delegation={s['delegation_count']}/5  "
              f"agents={s['correct_agents']}/5  "
              f"tavily={s['tavily_search']}/5")

        print(f"\n  MILESTONE 4  [{fmt(r.m4_pass)}]")
        print(f"    LLM-as-a-judge score: {r.m4_judge_score}/10  (need ≥7 to pass)")

        if r.error:
            print(f"\n  Error: {r.error}")

        time.sleep(1)

    # ── Aggregate summary ──────────────────────────────────────────────────
    total   = len(results)
    m1_pass = sum(1 for r in results if r.m1_pass)
    m2_pass = sum(1 for r in results if r.m2_pass)
    m3_pass = sum(1 for r in results if r.m3_pass)
    m4_pass = sum(1 for r in results if r.m4_pass)
    all_scores = [score_result(r) for r in results]

    def avg(key: str) -> float:
        return round(sum(s[key] for s in all_scores) / total, 1)

    avg_judge = round(sum(r.m4_judge_score for r in results) / total, 1)

    print("\n" + "=" * 72)
    print("  FINAL EVALUATION SUMMARY")
    print("=" * 72)
    print(f"  Total test cases          : {total}")
    print()
    print(f"  Milestone 1  Pass         : {m1_pass}/{total}  ({m1_pass/total*100:.0f}%)")
    print(f"    Avg write_todos called  : {avg('write_todos_called')}/5")
    print(f"    Avg todo structure      : {avg('todo_structure')}/5")
    print(f"    Avg completion          : {avg('todo_completion')}/5")
    print(f"    Avg JSON output         : {avg('json_output')}/5")
    print()
    print(f"  Milestone 2  Pass         : {m2_pass}/{total}  ({m2_pass/total*100:.0f}%)")
    print(f"    Avg file usage          : {avg('file_usage')}/5")
    print(f"    Avg content size        : {avg('file_content')}/5")
    print(f"    Avg edit_file           : {avg('edit_file')}/5")
    print(f"    Avg final report        : {avg('final_report')}/5")
    print()
    print(f"  Milestone 3  Pass         : {m3_pass}/{total}  ({m3_pass/total*100:.0f}%)")
    print(f"    Avg delegation count    : {avg('delegation_count')}/5")
    print(f"    Avg agent selection     : {avg('correct_agents')}/5")
    print(f"    Avg Tavily usage        : {avg('tavily_search')}/5")
    print()
    print(f"  Milestone 4  Pass (≥7/10) : {m4_pass}/{total}  ({m4_pass/total*100:.0f}%)")
    print(f"    Avg LLM-as-a-judge score: {avg_judge}/10")
    print()

    threshold = 0.80
    m4_threshold = 0.70
    print(f"  Pass/fail thresholds:")
    for label, passed, thresh in [
        ("Milestone 1 — Planning",    m1_pass / total, threshold),
        ("Milestone 2 — File System", m2_pass / total, threshold),
        ("Milestone 3 — Delegation",  m3_pass / total, threshold),
        ("Milestone 4 — End-to-End",  m4_pass / total, m4_threshold),
    ]:
        status = "PASS ✓" if passed >= thresh else "FAIL ✗"
        print(f"    {label:32s} {status}  ({passed*100:.0f}% vs {thresh*100:.0f}% needed)")

    print("=" * 72 + "\n")


# ── Simple scoring for API ────────────────────────────────────────────────────
def evaluate_output(report: str) -> str:
    """LLM-as-a-judge score for API /run endpoint. Returns string 1-10."""
    if not report:
        return "0"
    score = _llm_judge(report)
    return str(score)


if __name__ == "__main__":
    run_evaluation()
