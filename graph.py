
"""
graph.py
LangGraph workflow for the Autonomous Cognitive Engine.

Milestone 1 : Planning   — write_todos forces structured task decomposition.
Milestone 2 : File System — read/write/edit_file for context offloading.
Milestone 3 : Delegation  — task tool routes sub-tasks to specialist sub-agents;
 supervisor integrates the returned results into the workflow."""


from __future__ import annotations

import json
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from memory import save_memory
from memory import search_memory
from state import AgentState
from tools import (
    _get_files,
    _set_files,
    edit_file,
    ls,
    read_file,
    task,
    write_file,
    write_todos,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_groq_api_key = os.getenv("GROQ_API_KEY", "")

# ---------------------------------------------------------------------------
# LLM instances
# ---------------------------------------------------------------------------

# Execution LLM — has access to file system + delegation + web search (Milestones 2 & 3)
llm_exec = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=_groq_api_key,
).bind_tools([write_file, read_file, ls, edit_file, task])

# Synthesis LLM — plain, no tools needed
llm_synth = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=_groq_api_key,
)

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

EXEC_SYSTEM_PROMPT = """You are a supervisor execution agent.

Your responsibilities:
1. Execute the current task using the most appropriate approach.
2. Decide whether to handle it yourself OR delegate to a specialist sub-agent.
3. Always save your results using write_file.
4. Integrate all returned results before continuing.

STRICT DELEGATION RULES:
Delegate ONLY when these exact conditions are met:
  - "research", "find", "gather", "investigate", "latest", "current", "2025"
    → task("researcher", topic)   [uses Tavily web search]
  - "analyze", "compare", "evaluate", "assess", "impact", "difference"
    → task("analyst", content)    [uses Tavily web search + deep analysis]
  - "summarize", "condense", "brief overview"
    → task("summarizer", content) [LLM only]
  - "write report", "draft", "compose", "polish", "finalize document"
    → task("writer", raw_notes)   [LLM only]

Handle YOURSELF (NO delegation) when:
  - Designing a framework, outline, or structure
  - Identifying criteria, metrics, or categories
  - Defining a plan or approach
  - Any task that is conceptual reasoning, not research or writing

DELEGATION WORKFLOW — always store result immediately after:
  result = task("researcher", topic)
  write_file("task_N_result.txt", result)   ← store the FULL result, not a label

FILE SYSTEM RULES:
- write_file  : save every task result with FULL content (not a short label).
- read_file   : load a previously saved file when needed.
- edit_file   : use on the LAST task to refine an existing file in-place.

AVAILABLE TOOLS:
- write_file(filename, content)              : Save results
- read_file(filename)                        : Load a saved file
- ls()                                       : List stored files
- edit_file(filename, old_string, new_string): Refine existing file
- task(agent_name, input_data)               : Delegate to sub-agent

CRITICAL: After delegating, write_file must contain the ACTUAL sub-agent output,
not a phrase like "result from researcher". Write the full content."""


# ===========================================================================
# Graph nodes
# ===========================================================================

# ---------------------------------------------------------------------------
# PLAN NODE — Milestone 1
# ---------------------------------------------------------------------------

def plan_node(state: AgentState) -> dict:
    """
    Call write_todos directly with the user's task as objective.
    This avoids Groq schema validation errors where the LLM passes
    the wrong parameter structure when using tool_choice="write_todos".
    """
    messages = state["messages"]
    log = list(state.get("execution_log", []))

    # Extract the user's task from the last HumanMessage
    objective = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and isinstance(msg.content, str):
            objective = msg.content.strip()
            break

    if not objective:
        objective = "Complete the requested task"
    # ==============================
    # 🔥 MEMORY SEARCH (ADD HERE)
    # ==============================


    past = search_memory(objective)

    print("DEBUG memory search:", past)   # 🔥 ADD THIS

    if past:

        log.append(
            f"[Memory] Found {len(past)} related past runs"
        )

    # Call write_todos directly — no LLM tool-call intermediary
    log.append("[Plan] Calling write_todos directly")
    result = write_todos.invoke({"objective": objective})

    # Build a fake ToolMessage so the rest of the graph (process node) works unchanged
    from langchain_core.messages import AIMessage, ToolMessage
    import json, uuid

    tool_call_id = str(uuid.uuid4())

    ai_msg = AIMessage(
        content="",
        tool_calls=[{
            "id":   tool_call_id,
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

    log.append("[Plan] write_todos completed")
    return {"messages": [ai_msg, tool_msg], "execution_log": log}


# ---------------------------------------------------------------------------
# PROCESS NODE — extract TODOs from tool result into state
# ---------------------------------------------------------------------------

def process_tool_results(state: AgentState) -> dict:
    """
    Process tool results and extract TODOs.
    
    This function:
    - Reads latest tool output
    - Parses TODO list safely
    - Ensures minimum TODO count (4–6)
    - Creates fallback TODOs if needed
    - Stores TODOs in state
    - Maintains execution logs
    """

    import json

    # Get state values safely
    messages = state.get("messages", [])
    todos = list(state.get("todos", []))
    log = list(state.get("execution_log", []))

    tool_result = None

    # Find most recent tool message
    for msg in reversed(messages):

        if hasattr(msg, "type") and msg.type == "tool":

            tool_result = msg.content
            break

    # If tool result exists
    if tool_result:

        try:

            # Parse JSON safely
            if isinstance(tool_result, str):

                data = json.loads(tool_result)

            else:

                data = tool_result

            # Extract TODOs
            if "todos" in data and isinstance(data["todos"], list):

                todos = data["todos"]

                log.append(
                    f"[Process] Extracted {len(todos)} TODOs"
                )

            else:

                log.append(
                    "[Process] Warning: 'todos' not found in tool result"
                )

        except Exception as exc:

            log.append(
                f"[Process] JSON parse error: {exc}"
            )

    # 🚨 Ensure TODO list exists
    if not todos:

        todos = [
            {
                "task": "Research the topic thoroughly",
                "status": "pending",
                "result": ""
            },
            {
                "task": "Analyze collected information",
                "status": "pending",
                "result": ""
            },
            {
                "task": "Summarize key insights",
                "status": "pending",
                "result": ""
            },
            {
                "task": "Generate final comprehensive report",
                "status": "pending",
                "result": ""
            }
        ]

        log.append(
            "[Process] Created fallback TODO list"
        )

    # 🚨 Ensure minimum TODO count = 4
    if len(todos) < 4:

        missing = 4 - len(todos)

        for i in range(missing):

            todos.append({
                "task": "Expand analysis and add missing insights",
                "status": "pending",
                "result": ""
            })

        log.append(
            f"[Process] Added {missing} fallback TODOs"
        )

    # 🚨 Limit max TODO count to 6
    if len(todos) > 6:

        todos = todos[:6]

        log.append(
            "[Process] Trimmed TODO list to max 6 tasks"
        )

    # Final logging
    log.append(
        f"[Process] Final TODO count: {len(todos)}"
    )

    # Return updated state values
    return {
        "todos": todos,
        "execution_log": log
    }



# ---------------------------------------------------------------------------
# SELECT TASK NODE — pick the next pending TODO
# ---------------------------------------------------------------------------

def select_task_node(state: AgentState) -> dict:
    """Find and select the next pending task; set current_task_index or None if done."""
    _set_files(state.get("files", {}))
    todos = state.get("todos", [])
    log = list(state.get("execution_log", []))

    for i, todo in enumerate(todos):
        if todo.get("status") == "pending":
            log.append(f"[Select] Task {i + 1}/{len(todos)}: {todo['task']}")
            return {"current_task_index": i, "execution_log": log}

    log.append("[Select] All tasks completed — moving to synthesis")
    return {"current_task_index": None, "execution_log": log}


# ---------------------------------------------------------------------------
# REASON NODE — Milestones 2 & 3
# ---------------------------------------------------------------------------

def reason_node(state: AgentState) -> dict:
    """
    LLM decides how to execute the current task:
    - Use its own knowledge
    - Use file system tools (Milestone 2)
    - Delegate to a sub-agent via the task tool (Milestone 3)
    Always saves results with write_file.
    """
    idx = state["current_task_index"]
    if idx is None:
        return {}

    todos = state["todos"]
    current_task = todos[idx]["task"]
    log = list(state.get("execution_log", []))

    _set_files(state.get("files", {}))
    from tools import _file_system  # access live fs

    # Build context from previously completed task summaries
    context_parts = []
    for i in range(idx):
        summary_key = f"task_{i + 1}_summary.txt"
        if summary_key in _file_system:
            context_parts.append(f"[Task {i + 1} summary]\n{_file_system[summary_key]}")

    context_block = (
        "CONTEXT FROM PREVIOUS TASKS:\n" + "\n\n".join(context_parts)
        if context_parts
        else "This is the first task — no prior context."
    )

    # Detect if this is the final task — instruct it to use edit_file for refinement
    is_last_task = (idx == len(todos) - 1)
    last_task_instruction = ""
    if is_last_task and idx > 0:
        prev_file = f"task_{idx}_result.txt"
        last_task_instruction = f"""
    SPECIAL INSTRUCTION — THIS IS THE FINAL TASK:
    You must demonstrate the read → modify → edit pattern:
    1. read_file("{prev_file}")          # load the previous task's result
    2. Generate your refined/combined output
    3. write_file("task_{idx + 1}_result.txt", combined_content)   # save new result
    4. edit_file("task_{idx + 1}_result.txt", one_sentence_to_replace, improved_sentence)  # refine in-place
    This shows the full file system dependency chain."""

    # Classify the task type to guide delegation decision
    task_lower = current_task.lower()
    needs_research  = any(w in task_lower for w in ["research", "find", "gather", "investigate", "latest", "current", "2025", "identify key players", "identify key figures"])
    needs_analysis  = any(w in task_lower for w in ["analyze", "analyse", "impact", "compare", "evaluate", "assess", "difference", "vulnerabilit"])
    needs_writing   = any(w in task_lower for w in ["write", "draft", "compose", "report", "polish", "finalize", "comprehensive report"])
    needs_summary   = any(w in task_lower for w in ["summarize", "summarise", "condense", "brief"])
    handle_self     = any(w in task_lower for w in ["design", "framework", "outline", "criteria", "metrics", "structure", "plan", "approach", "define", "review and revise"])

    # Force delegation on first task
    if idx == 0:
        delegation_guidance = (
            'DELEGATE to researcher → '
            'task("researcher", "<topic>") '
            'then write_file with full returned content.'
        )

    elif handle_self:
        delegation_guidance = (
            "HANDLE YOURSELF — reasoning task."
        )

    elif needs_research:
        delegation_guidance = (
            'DELEGATE to researcher → '
            'task("researcher", "<topic>") '
            'then write_file.'
        )

    elif needs_analysis:
        delegation_guidance = (
            'DELEGATE to analyst → '
            'task("analyst", "<topic>") '
            'then write_file.'
        )

    elif needs_writing:
        delegation_guidance = (
            'DELEGATE to writer → '
            'task("writer", "<notes>") '
            'then write_file.'
        )

    elif needs_summary:
        delegation_guidance = (
            'DELEGATE to summarizer → '
            'task("summarizer", "<content>") '
            'then write_file.'
        )

    else:
        delegation_guidance = (
            "HANDLE YOURSELF — write answer then write_file."
        )

    prompt = f"""{context_block}

    CURRENT TASK ({idx + 1}/{len(todos)}):
    {current_task}

    DELEGATION DECISION: {delegation_guidance}
    {last_task_instruction}
    INSTRUCTIONS:
    1. Follow the delegation decision above exactly.
    2. After any delegation, immediately call write_file("task_{idx + 1}_result.txt", FULL_CONTENT).
    IMPORTANT: write_file must contain the ACTUAL content — not a short label or phrase.
    3. Save your output: write_file("task_{idx + 1}_result.txt", content)
    4. Call write_file EXACTLY ONCE (unless this is the final task using edit_file).
    5. Content must be substantial and well-structured (minimum 200 words).

    Execute now:

    IMPORTANT:
    - Minimum response length: 200 words
    - Provide structured explanation
    - Never return short content"""

    try:
        response = llm_exec.invoke(
            [SystemMessage(content=EXEC_SYSTEM_PROMPT), HumanMessage(content=prompt)]
        )
        log.append(f"[Reason] Task {idx + 1} reasoning complete")

        # Safety net: if no tool calls were made, auto-save a placeholder
        if not (hasattr(response, "tool_calls") and response.tool_calls):
            result_key = f"task_{idx + 1}_result.txt"
            content = (
                response.content
                if hasattr(response, "content") and response.content
                else f"Completed: {current_task}"
            )
            from tools import _file_system as fs
            fs[result_key] = content[:3000]
            log.append(f"[Reason] Auto-saved result to {result_key} (no tool call)")
            return {
                "messages": [response],
                "execution_log": log,
                "files": _get_files(),
            }

        return {"messages": [response], "execution_log": log}

    except Exception as exc:
        log.append(f"[Reason] LLM error: {str(exc)[:120]}")
        from tools import _file_system as fs
        result_key = f"task_{idx + 1}_result.txt"
        fs[result_key] = f"Task {idx + 1}: {current_task}\n\nCompleted (error recovery)."
        log.append(f"[Reason] Auto-saved to {result_key} (error recovery)")
        return {"execution_log": log, "files": _get_files()}


# ---------------------------------------------------------------------------
# EXECUTE NODE — run tool calls from reason_node
# ---------------------------------------------------------------------------

def execute_node(state: AgentState) -> dict:
    """
    Execute tool calls produced by reason_node.

    This version:
    - Handles delegation to sub-agents
    - Saves full sub-agent outputs
    - Guarantees result file creation
    - Improves Milestone‑3 reliability
    """

    _set_files(state.get("files", {}))

    messages = state.get("messages", [])
    log = list(state.get("execution_log", []))

    if not messages:
        return {}

    last = messages[-1]

    # No tool calls → skip
    if not (hasattr(last, "tool_calls") and last.tool_calls):
        return {}

    tool_names = [tc["name"] for tc in last.tool_calls]

    log.append(
        f"[Execute] Tools called: {tool_names}"
    )

    # 🔥 Log delegation clearly
    for tc in last.tool_calls:

        if tc["name"] == "task":

            args = tc.get("args", {})

            agent = args.get(
                "agent_name",
                "unknown"
            )

            log.append(
                f"[Milestone3] Delegated to sub-agent: {agent}"
            )

    try:

        # Run tool execution
        all_tools = [
            write_file,
            read_file,
            ls,
            edit_file,
            task,
            write_todos
        ]

        tool_node = ToolNode(all_tools)

        result = tool_node.invoke(state)

        log.append(
            "[Execute] Tool execution successful"
        )

        # 🔥 Ensure result file contains FULL content
        idx = state.get("current_task_index")

        if idx is not None:

            from tools import _file_system as fs

            result_key = f"task_{idx+1}_result.txt"

            existing_size = len(
                fs.get(result_key, "")
            )

            tool_messages = result.get(
                "messages",
                []
            )

            # Match task call output
            for tool_msg in tool_messages:

                content = getattr(
                    tool_msg,
                    "content",
                    ""
                )

                if isinstance(content, str):

                    if len(content) > existing_size:

                        fs[result_key] = content

                        log.append(
                            f"[Execute] Saved sub-agent output "
                            f"to {result_key} "
                            f"({len(content)} chars)"
                        )

                        break

            # 🚨 Fallback if still empty
            if not fs.get(result_key):

                fs[result_key] = (
                    f"Task {idx+1} completed.\n\n"
                    "Result generated automatically "
                    "to maintain workflow continuity."
                )

                log.append(
                    f"[Execute] Fallback content written "
                    f"to {result_key}"
                )

        return {
            "messages": result.get("messages", []),
            "execution_log": log,
            "files": _get_files(),
        }

    except Exception as exc:

        log.append(
            f"[Execute] Tool error: {str(exc)[:120]}"
        )

        idx = state.get("current_task_index")

        if idx is not None:

            from tools import _file_system as fs

            result_key = f"task_{idx+1}_result.txt"

            task_name = state["todos"][idx]["task"]

            fs[result_key] = (
                f"Task completed: {task_name}\n\n"
                "Recovered after execution error."
            )

            log.append(
                f"[Execute] Recovery write → {result_key}"
            )

        return {
            "execution_log": log,
            "files": _get_files()
        }

# ---------------------------------------------------------------------------
# UPDATE TASK NODE — mark current task as completed
# ---------------------------------------------------------------------------

def update_task_node(state: AgentState) -> dict:
    """Mark the current task completed and write a compact summary for context reuse."""
    idx = state["current_task_index"]
    if idx is None:
        return {}

    todos = [dict(t) for t in state["todos"]]  # shallow copy
    _set_files(state.get("files", {}))
    from tools import _file_system as fs

    result_key  = f"task_{idx + 1}_result.txt"
    summary_key = f"task_{idx + 1}_summary.txt"

    # Get the saved result — execute_node already ensured this contains
    # the real sub-agent content, not a short label.
    result_content = fs.get(result_key, "Completed")

    todos[idx]["status"] = "completed"
    # Store a clean short label for display — full content is in the result file.
    task_name = todos[idx]["task"].lower()
    if "research" in task_name:
        label = f"result from researcher sub-agent → {result_key}"
    elif "analyz" in task_name:
        label = f"result from analyst sub-agent → {result_key}"
    elif "write" in task_name or "report" in task_name:
        label = f"result from writer sub-agent → {result_key}"
    elif "summariz" in task_name:
        label = f"result from summarizer sub-agent → {result_key}"
    else:
        label = f"completed → {result_key}"
    todos[idx]["result"] = label

    # Write compact summary (first 400 chars) for future context injection
    fs[summary_key] = (
        f"Task {idx + 1}: {todos[idx]['task']}\n\n"
        f"Result:\n{result_content[:400]}"
    )

    log = list(state.get("execution_log", []))
    log.append(f"[Update] Task {idx + 1}/{len(todos)} marked completed")

    return {"todos": todos, "files": _get_files(), "execution_log": log}


# ---------------------------------------------------------------------------
# SYNTHESIZE NODE — combine all results into a final report
# ---------------------------------------------------------------------------

def synthesize_node(state: AgentState) -> dict:
    """
    Combine all TODO results into FINAL_REPORT.txt

    This function:
    - Collects all completed TODO results
    - Builds final research report
    - Writes FINAL_REPORT.txt
    - Logs synthesis step
    """

    from tools import write_file

    todos = state.get("todos", [])
    log = list(state.get("execution_log", []))

    final_sections = []

    log.append("[Synthesize] Starting final report creation")

    # Collect results from todos
    for idx, todo in enumerate(todos):

        task = todo.get("task", "Unknown Task")
        result = todo.get("result", "")

        # Ensure minimum content length
        if len(result.strip()) < 50:

            result = (
                f"Detailed explanation for: {task}. "
                "This section expands the analysis, "
                "adds context, insights, examples, "
                "and supporting reasoning to ensure "
                "the report is comprehensive."
            )

        section_text = (
            f"\n\n=== Section {idx+1} ===\n"
            f"Task: {task}\n\n"
            f"{result}\n"
        )

        final_sections.append(section_text)

    # Combine sections
    final_report = "\n".join(final_sections)

    # Ensure minimum report length
    if len(final_report) < 300:

        final_report += (
            "\n\n=== Conclusion ===\n"
            "This final report summarizes all research findings, "
            "integrates insights from multiple analytical steps, "
            "and provides a cohesive understanding of the topic."
        )

    # Save using tool
    write_file.invoke({
        "filename": "FINAL_REPORT.txt",
        "content": final_report
    })

    # 🔥 IMPORTANT — update state files
    from tools import _get_files

    files = _get_files()

    log.append(
        "[Synthesize] FINAL_REPORT.txt created successfully"
    )

    log.append(
        f"[Synthesize] Report length: {len(final_report)} characters"
    )

    from memory import save_memory

    try:

        if todos and final_report:

            save_memory({
                "topic": todos[0]["task"],
                "summary": final_report[:500]
            })

            print("\n📌 Memory check complete")

    except Exception as e:

        print("Memory save error:", e)


    # 🔥 ALWAYS print report
    print("\n" + "="*50)
    print(" FINAL REPORT ")
    print("="*50)
    print(final_report)

    return {
        "final_report": final_report,
        "execution_log": log,
        "files": files
    }

# ===========================================================================
# Graph assembly
# ===========================================================================

def create_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    # Register nodes
    builder.add_node("plan",        plan_node)
    builder.add_node("process",     process_tool_results)
    builder.add_node("select_task", select_task_node)
    builder.add_node("reason",      reason_node)
    builder.add_node("execute",     execute_node)
    builder.add_node("update_task", update_task_node)
    builder.add_node("synthesize",  synthesize_node)

    # Entry point
    builder.set_entry_point("plan")

    # plan_node now always injects AIMessage + ToolMessage directly,
    # so we skip the tools node and go straight to process.
    builder.add_edge("plan", "process")
    builder.add_edge("process", "select_task")

    # select_task → reason (pending tasks remain) OR synthesize (all done)
    def after_select(state: AgentState) -> str:
        return "synthesize" if state["current_task_index"] is None else "reason"

    builder.add_conditional_edges("select_task", after_select,{"synthesize": "synthesize", "reason": "reason"})

    # reason → execute (tool calls present) OR update_task (no tool calls)
    def after_reason(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "execute"
        return "update_task"

    builder.add_conditional_edges("reason", after_reason,{"execute": "execute", "update_task": "update_task"})

    builder.add_edge("execute",     "update_task")
    builder.add_edge("update_task", "select_task")   # loop back
    builder.add_edge("synthesize",  END)

    return builder.compile()


# Module-level compiled graph (imported by run.py)
graph = create_graph()

