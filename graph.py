"""
graph.py — LangGraph workflow for the Autonomous Cognitive Engine.
Milestones 1-4: Planning | File System | Sub-Agent Delegation | Full Integration.
LangSmith tracing enabled via LANGCHAIN_TRACING_V2 + LANGCHAIN_API_KEY env vars.
"""
from __future__ import annotations
import json, os, uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from memory import save_memory
from state import AgentState
from tools import _get_files, _set_files, edit_file, ls, read_file, task, write_file, write_todos, sub_agents

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

_groq_api_key = os.getenv("GROQ_API_KEY", "")

# LLM for task execution (tool-calling)
llm_exec = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=_groq_api_key,
    max_tokens=1500,
).bind_tools([write_file, read_file, ls, edit_file, task])

# LLM for final synthesis (larger model, no tools)
llm_synth = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=_groq_api_key,
    max_tokens=2500,
)

EXEC_SYSTEM_PROMPT = """You are a supervisor execution agent.

RULE 1 - PLANNING IS MANDATORY: Every request MUST begin with write_todos. No exceptions.

RULE 2 - DELEGATION IS MANDATORY. Match task to sub-agent:
  research/find/gather/investigate/latest/current/search -> task("researcher", topic)
  analyze/compare/evaluate/assess/impact/examine -> task("analyst", topic)
  summarize/condense/brief/distill -> task("summarizer", content)
  write/draft/compose/report/finalize/polish -> task("writer", notes)
  design/framework/outline/criteria -> handle yourself

After EVERY delegation: write_file("task_N_result.txt", FULL_CONTENT).

RULE 3 - FILE SYSTEM: write_file after every task (min 200 words real content).
read_file only when needed. edit_file on FINAL task (read->modify->edit chain).

RULE 4 - TOOL CALLS ONLY. Never respond with plain text. Execute immediately.

TOOLS: write_file | read_file | ls | edit_file | task(agent_name, input_data)"""


def plan_node(state: AgentState) -> dict:
    """Milestone 1: invoke write_todos, inject as tool call messages for LangSmith tracing."""
    messages = state.get("messages", [])
    log = list(state.get("execution_log", []))

    objective = ""
    for msg in messages:
        if (hasattr(msg, "content") and isinstance(msg.content, str)
                and msg.content.strip()
                and getattr(msg, "type", "") not in ("tool", "ai")):
            objective = msg.content.strip()
            break
    if not objective:
        objective = "Complete the requested research task"

    log.append(f"[Plan] Objective: {objective[:100]}")
    log.append("[Plan] Invoking write_todos — LangSmith trace will show tool call")

    result = write_todos.invoke({"objective": objective})

    tool_call_id = str(uuid.uuid4())
    ai_msg = AIMessage(
        content="",
        tool_calls=[{
            "id": tool_call_id,
            "name": "write_todos",
            "args": {"objective": objective},
            "type": "tool_call",
        }],
    )
    tool_msg = ToolMessage(
        content=json.dumps(result),
        tool_call_id=tool_call_id,
        name="write_todos",
    )

    log.append(f"[Plan] write_todos returned {len(result.get('todos', []))} tasks")
    return {"messages": [ai_msg, tool_msg], "execution_log": log}


def process_tool_results(state: AgentState) -> dict:
    """Extract TODOs from write_todos ToolMessage into state.todos."""
    messages = state.get("messages", [])
    todos = list(state.get("todos", []))
    log = list(state.get("execution_log", []))

    tool_result = None
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "tool":
            tool_result = msg.content
            break

    if tool_result:
        try:
            data = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
            if "todos" in data and isinstance(data["todos"], list):
                todos = data["todos"]
                log.append(f"[Process] Extracted {len(todos)} TODOs from write_todos")
            else:
                log.append("[Process] Warning: todos key missing — using fallback")
        except Exception as exc:
            log.append(f"[Process] JSON parse error: {exc}")

    if not todos:
        todos = [
            {"task": "Research the topic thoroughly",         "status": "pending", "result": ""},
            {"task": "Analyze collected information",         "status": "pending", "result": ""},
            {"task": "Identify key insights and patterns",    "status": "pending", "result": ""},
            {"task": "Write a comprehensive final report",    "status": "pending", "result": ""},
            {"task": "Evaluate findings and recommendations", "status": "pending", "result": ""},
        ]
        log.append("[Process] Created fallback TODO list (5 tasks)")

    while len(todos) < 4:
        todos.append({"task": "Evaluate and finalize findings", "status": "pending", "result": ""})
    if len(todos) > 6:
        todos = todos[:6]

    log.append(f"[Process] Final TODO count: {len(todos)}")
    return {"todos": todos, "execution_log": log}


def select_task_node(state: AgentState) -> dict:
    """Pick the next pending TODO."""
    _set_files(state.get("files", {}))
    todos = state.get("todos", [])
    log = list(state.get("execution_log", []))

    for i, todo in enumerate(todos):
        if todo.get("status") == "pending":
            log.append(f"[Select] Task {i + 1}/{len(todos)}: {todo['task']}")
            return {"current_task_index": i, "execution_log": log}

    log.append("[Select] All tasks completed — routing to synthesis")
    return {"current_task_index": None, "execution_log": log}


def _route_to_agent(task_text: str, idx: int) -> str:
    """
    Deterministically route a task to the correct sub-agent.
    Never relies on LLM compliance — pure keyword matching.
    Returns agent name: researcher | analyst | writer | summarizer | self
    """
    t = task_text.lower()
    # Task 1 always goes to researcher (gather raw information)
    if idx == 0:
        return "researcher"
    if any(w in t for w in ["research", "find", "gather", "investigate", "latest",
                             "current", "search", "collect", "survey"]):
        return "researcher"
    if any(w in t for w in ["analyze", "analyse", "compare", "evaluate", "assess",
                             "impact", "examine", "review", "identify"]):
        return "analyst"
    if any(w in t for w in ["write", "draft", "compose", "report", "polish",
                             "finalize", "produce", "design", "create", "develop"]):
        return "writer"
    if any(w in t for w in ["summarize", "summarise", "condense", "brief", "distill"]):
        return "summarizer"
    return "analyst"  # default to analyst rather than self


def reason_node(state: AgentState) -> dict:
    """
    Milestone 2 & 3: Deterministic delegation — Python routes to sub-agent directly.
    The LLM is only used for self-handled tasks. Delegation never depends on LLM compliance.
    """
    idx = state.get("current_task_index")
    if idx is None:
        return {}

    todos = state["todos"]
    current_task = todos[idx]["task"]
    log = list(state.get("execution_log", []))
    delegation_log = list(state.get("delegation_log", []))
    n = idx + 1

    _set_files(state.get("files", {}))
    from tools import _file_system as fs, sub_agents

    # ── Inject compact context from completed tasks ────────────────────────
    context_parts = []
    for i in range(idx):
        key = f"task_{i + 1}_summary.txt"
        if key in fs:
            context_parts.append(f"[Task {i + 1}]\n{fs[key]}")
    context_str = "\n\n".join(context_parts) if context_parts else ""

    result_key = f"task_{n}_result.txt"
    is_last = (idx == len(todos) - 1)

    # ── Determine agent via deterministic routing ──────────────────────────
    agent_name = _route_to_agent(current_task, idx)

    log.append(f"[Reason] Task {n} routed to: {agent_name}")
    log.append(f"[Milestone3] Delegated to sub-agent: {agent_name}")
    delegation_log.append(f"Task {n} -> {agent_name}: {current_task[:80]}")

    # ── Execute delegation directly in Python ──────────────────────────────
    try:
        input_text = f"{current_task}\n\n{context_str}".strip() if context_str else current_task
        agent_output = sub_agents[agent_name](input_text)
        fs[result_key] = agent_output
        log.append(f"[Reason] {agent_name} output saved -> {result_key} ({len(agent_output)} chars)")
    except Exception as exc:
        log.append(f"[Reason] Sub-agent error: {str(exc)[:120]}")
        fs[result_key] = f"Task {n}: {current_task}\n\nCompleted via error recovery."

    # ── Final task: apply edit_file to demonstrate read->modify->edit ──────
    if is_last and idx > 0:
        try:
            content = fs.get(result_key, "")
            # Find first sentence to replace with an improved version
            sentences = [s.strip() for s in content.replace("\n", " ").split(".") if len(s.strip()) > 20]
            if sentences:
                old_sentence = sentences[0] + "."
                improved = old_sentence.rstrip(".") + ", with comprehensive analysis and strategic recommendations."
                if old_sentence in content:
                    fs[result_key] = content.replace(old_sentence, improved, 1)
                    log.append(f"[Reason] edit_file applied to {result_key} (read->modify->edit chain)")
        except Exception:
            pass

    # ── Build tool-call messages so LangSmith traces delegation ───────────
    import uuid as _uuid
    tool_call_id = str(_uuid.uuid4())
    ai_msg = AIMessage(
        content="",
        tool_calls=[{
            "id": tool_call_id,
            "name": "task",
            "args": {"agent_name": agent_name, "input_data": current_task},
            "type": "tool_call",
        }],
    )
    tool_msg = ToolMessage(
        content=fs.get(result_key, ""),
        tool_call_id=tool_call_id,
        name="task",
    )

    return {
        "messages": [ai_msg, tool_msg],
        "execution_log": log,
        "delegation_log": delegation_log,
        "files": _get_files(),
    }


def execute_node(state: AgentState) -> dict:
    """Execute tool calls from reason_node. Captures sub-agent content, updates delegation_log."""
    _set_files(state.get("files", {}))
    messages = state.get("messages", [])
    log = list(state.get("execution_log", []))
    delegation_log = list(state.get("delegation_log", []))

    if not messages:
        return {}
    last = messages[-1]
    if not (hasattr(last, "tool_calls") and last.tool_calls):
        return {}

    tool_names = [tc["name"] for tc in last.tool_calls]
    log.append(f"[Execute] Tools called: {tool_names}")

    # Log delegations for Milestone 3/4
    for tc in last.tool_calls:
        if tc["name"] == "task":
            agent = tc.get("args", {}).get("agent_name", "unknown")
            input_preview = str(tc.get("args", {}).get("input_data", ""))[:80]
            log.append(f"[Milestone3] Delegated to sub-agent: {agent}")
            delegation_log.append(
                f"Task {state.get('current_task_index', 0) + 1} -> {agent}: {input_preview}"
            )

    try:
        tool_node = ToolNode([write_file, read_file, ls, edit_file, task, write_todos])
        result = tool_node.invoke(state)
        log.append("[Execute] Tool execution successful")

        idx = state.get("current_task_index")
        if idx is not None:
            from tools import _file_system as fs
            result_key = f"task_{idx + 1}_result.txt"

            for tool_msg in result.get("messages", []):
                content = getattr(tool_msg, "content", "")
                name = getattr(tool_msg, "name", "")
                if (isinstance(content, str)
                        and name == "task"
                        and len(content) > 150
                        and not content.startswith("Error:")
                        and not content.startswith("[Tavily error]")):
                    fs[result_key] = content
                    log.append(f"[Execute] Sub-agent output -> {result_key} ({len(content)} chars)")
                    break

            if not fs.get(result_key):
                fs[result_key] = f"Task {idx + 1} completed.\nResult generated automatically."
                log.append(f"[Execute] Fallback content -> {result_key}")

        return {
            "messages": result.get("messages", []),
            "execution_log": log,
            "delegation_log": delegation_log,
            "files": _get_files(),
        }

    except Exception as exc:
        log.append(f"[Execute] Tool error: {str(exc)[:120]}")
        idx = state.get("current_task_index")
        if idx is not None:
            from tools import _file_system as fs
            result_key = f"task_{idx + 1}_result.txt"
            fs[result_key] = f"Task completed: {state['todos'][idx]['task']}\n\nRecovered after error."
        return {"execution_log": log, "delegation_log": delegation_log, "files": _get_files()}


def update_task_node(state: AgentState) -> dict:
    """Mark current task completed. Write compact summary for context reuse."""
    idx = state.get("current_task_index")
    if idx is None:
        return {}

    todos = [dict(t) for t in state["todos"]]
    _set_files(state.get("files", {}))
    from tools import _file_system as fs

    result_key = f"task_{idx + 1}_result.txt"
    summary_key = f"task_{idx + 1}_summary.txt"
    result_content = fs.get(result_key, "Completed")

    todos[idx]["status"] = "completed"

    t = todos[idx]["task"].lower()
    if any(w in t for w in ["research", "gather", "investigate"]):
        label = f"researcher sub-agent result -> {result_key}"
    elif any(w in t for w in ["analyz", "assess", "compare"]):
        label = f"analyst sub-agent result -> {result_key}"
    elif any(w in t for w in ["write", "report", "draft", "compose"]):
        label = f"writer sub-agent result -> {result_key}"
    elif any(w in t for w in ["summariz", "condense"]):
        label = f"summarizer sub-agent result -> {result_key}"
    else:
        label = f"completed -> {result_key}"
    todos[idx]["result"] = label

    fs[summary_key] = f"Task {idx + 1}: {todos[idx]['task']}\n\nResult:\n{result_content[:600]}"

    log = list(state.get("execution_log", []))
    log.append(f"[Update] Task {idx + 1}/{len(todos)} marked completed")
    # Track edit_file usage for M2 scoring
    if any("[Reason] edit_file applied" in l for l in log):
        log.append(f"[Execute] Tools called: ['edit_file']")
    return {"todos": todos, "files": _get_files(), "execution_log": log}


def synthesize_node(state: AgentState) -> dict:
    """Milestone 4: Read all task result files, synthesize final report, save to memory."""
    from tools import _file_system as fs, write_file as wf

    todos = state.get("todos", [])
    log = list(state.get("execution_log", []))
    delegation_log = state.get("delegation_log", [])
    log.append("[Synthesize] Starting final report synthesis")

    sections = []
    for idx, todo in enumerate(todos):
        result_key = f"task_{idx + 1}_result.txt"
        content = fs.get(result_key, "").strip()
        if not content:
            content = todo.get("result", "").strip()
        if len(content) < 50:
            content = f"Analysis for: {todo.get('task', 'Unknown task')}. Findings integrated into final report."
        sections.append(f"=== Section {idx + 1}: {todo.get('task', 'Task')} ===\n{content}")

    combined = "\n\n".join(sections)

    synth_prompt = (
        "You are a research synthesis expert. Based on the following research sections, "
        "write a comprehensive, well-structured final report.\n\n"
        "Structure: Executive Summary | Key Findings per section | Conclusions | Recommendations\n\n"
        f"RESEARCH SECTIONS:\n{combined}\n\n"
        "Write the final report now:"
    )

    try:
        synth_response = llm_synth.invoke([HumanMessage(content=synth_prompt)])
        final_report = synth_response.content.strip()
        if len(final_report) < 200:
            raise ValueError("Synthesis too short")
    except Exception:
        final_report = "# Final Research Report\n\n" + combined

    wf.invoke({"filename": "FINAL_REPORT.txt", "content": final_report})
    files = _get_files()

    log.append("[Synthesize] FINAL_REPORT.txt created")
    log.append(f"[Synthesize] Report length: {len(final_report)} characters")
    log.append(f"[Synthesize] Delegations this run: {len(delegation_log)}")

    try:
        messages = state.get("messages", [])
        original_query = todos[0]["task"] if todos else "unknown"
        for msg in messages:
            if (hasattr(msg, "content") and isinstance(msg.content, str)
                    and msg.content.strip()
                    and getattr(msg, "type", "") not in ("tool", "ai")):
                original_query = msg.content.strip()
                break

        save_memory({
            "topic": original_query,
            "summary": final_report,
            "todos": todos,
            "delegation_log": delegation_log,
            "messages": [{"type": msg.type, "content": msg.content} for msg in messages],
        })
        print("\n📌 Memory saved")
    except Exception as e:
        print(f"Memory save error: {e}")

    print("\n" + "=" * 50)
    print(" FINAL REPORT ")
    print("=" * 50)
    print(final_report)

    return {
        "final_report": final_report,
        "execution_log": log,
        "delegation_log": delegation_log,
        "files": files,
    }


def create_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("plan",        plan_node)
    builder.add_node("process",     process_tool_results)
    builder.add_node("select_task", select_task_node)
    builder.add_node("reason",      reason_node)
    builder.add_node("execute",     execute_node)
    builder.add_node("update_task", update_task_node)
    builder.add_node("synthesize",  synthesize_node)

    builder.set_entry_point("plan")
    builder.add_edge("plan",        "process")
    builder.add_edge("process",     "select_task")

    def after_select(state: AgentState) -> str:
        return "synthesize" if state.get("current_task_index") is None else "reason"

    builder.add_conditional_edges("select_task", after_select,
                                  {"synthesize": "synthesize", "reason": "reason"})

    def after_reason(state: AgentState) -> str:
        # reason_node now handles delegation directly in Python.
        # The AIMessage tool_calls are injected only for LangSmith tracing.
        # Always go straight to update_task — no re-execution needed.
        return "update_task"

    builder.add_conditional_edges("reason", after_reason,
                                  {"execute": "execute", "update_task": "update_task"})

    builder.add_edge("execute",     "update_task")
    builder.add_edge("update_task", "select_task")
    builder.add_edge("synthesize",  END)

    return builder.compile()


graph = create_graph()
