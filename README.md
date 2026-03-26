# Autonomous Cognitive Engine — Deep Research Agent

> **Enabling Long-Horizon Tasks with Memory, Planning, and Multi-Agent Collaboration**

A sophisticated, autonomous AI agent framework built with **LangGraph** that executes complex, multi-step research and reasoning tasks. The agent decomposes high-level objectives into structured plans, offloads context to a virtual file system, and delegates specialized sub-tasks to purpose-built sub-agents.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Milestones](#milestones)
  - [Milestone 1 — Structured Task Planning](#milestone-1--structured-task-planning-weeks-12)
  - [Milestone 2 — Context Offloading via Virtual File System](#milestone-2--context-offloading-via-virtual-file-system-weeks-34)
  - [Milestone 3 — Sub-Agent Delegation](#milestone-3--sub-agent-delegation-weeks-56)
- [Running the Agent](#running-the-agent)
- [Agent Workflow](#agent-workflow)
- [Evaluation](#evaluation)

---

## Project Overview

The **Autonomous Cognitive Engine** is a "Deep Cognitive Task Framework" that moves beyond simple tool-calling loops to support:

- **Structured planning** — breaks high-level objectives into ordered, actionable TODO lists
- **Context offloading** — stores intermediate results in a virtual file system to overcome LLM context-window limits
- **Sub-agent delegation** — routes specialized sub-tasks (research, analysis, summarization, writing) to dedicated agents
- **Stateful orchestration** — the entire workflow is managed as a LangGraph `StateGraph` with robust state tracking

---

## Architecture

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                  LangGraph StateGraph                │
│                                                     │
│  ┌──────┐   ┌─────────┐   ┌─────────────┐          │
│  │ Plan │──▶│ Process │──▶│ Select Task │◀─────┐   │
│  └──────┘   └─────────┘   └──────┬──────┘      │   │
│                                  │              │   │
│                            ┌─────▼──────┐       │   │
│                            │   Reason   │       │   │
│                            └─────┬──────┘       │   │
│                                  │              │   │
│                         ┌────────▼────────┐     │   │
│                         │     Execute     │     │   │
│                         │  ┌───────────┐  │     │   │
│                         │  │ File Tools│  │     │   │
│                         │  │   task()  │──┼──▶ Sub-Agents
│                         │  └───────────┘  │     │   │
│                         └────────┬────────┘     │   │
│                                  │              │   │
│                         ┌────────▼────────┐     │   │
│                         │  Update Task    │─────┘   │
│                         └─────────────────┘         │
│                                  │ (all done)        │
│                         ┌────────▼────────┐         │
│                         │   Synthesize    │         │
│                         └────────┬────────┘         │
└──────────────────────────────────┼─────────────────┘
                                   ▼
                            Final Report
```

**Sub-Agent Registry:**

| Agent | Trigger Keywords | Powered By |
|---|---|---|
| `researcher` | research, find, gather, investigate, latest | Tavily Search + LLM |
| `analyst` | analyze, compare, evaluate, assess, impact | Tavily Search + LLM |
| `summarizer` | summarize, condense, brief | LLM only |
| `writer` | write report, draft, compose, polish | LLM only |

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Agent Framework | LangGraph |
| LLM Integration | LangChain |
| LLM Provider | Groq (`llama-3.1-8b-instant`) |
| Web Search | Tavily API |
| Observability | LangSmith |
| Package Manager | `uv` (recommended) or `pip` |
| Environment Variables | `python-dotenv` |

---

## Project Structure

```
autonomous-cognitive-engine/
│
├── graph.py          # LangGraph workflow — all nodes and graph assembly
├── state.py          # AgentState TypedDict — shared state definition
├── tools.py          # All tool definitions (planning, file system, sub-agents)
├── run.py            # Main entry point — CLI runner with formatted output
│
├── .env              # API keys (not committed)
├── requirements.txt  # Python dependencies
└── README.md
```

### File Descriptions

**`state.py`** — Defines `AgentState`, the shared LangGraph state:
- `messages` — full conversation and tool call history
- `todos` — structured TODO list (`task`, `status`, `result`)
- `current_task_index` — index of the currently executing task (`None` when all done)
- `files` — virtual file system dictionary `{filename → content}`
- `execution_log` — human-readable trace of every major step

**`tools.py`** — All LangChain `@tool` definitions across all three milestones:
- `write_todos` (Milestone 1)
- `ls`, `read_file`, `write_file`, `edit_file` (Milestone 2)
- `task`, plus `_researcher_agent`, `_analyst_agent`, `_summarizer_agent`, `_writer_agent` (Milestone 3)

**`graph.py`** — The full LangGraph `StateGraph`:
- Nodes: `plan`, `process`, `select_task`, `reason`, `execute`, `update_task`, `synthesize`
- Conditional routing logic between nodes
- System prompts for the execution and synthesis LLMs

**`run.py`** — CLI entry point:
- Streams graph execution with live progress indicators
- Displays the task plan (JSON), file system summary, delegation log, and final report

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd autonomous-cognitive-engine
```

### 2. Create a virtual environment

Using `uv` (recommended):
```bash
uv venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
```

Using standard `venv`:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
# or
pip install -r requirements.txt
```

**Core dependencies:**
```
langgraph
langchain
langchain-groq
langchain-core
tavily-python
python-dotenv
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here     # optional, for tracing
LANGCHAIN_TRACING_V2=true                          # optional, enable LangSmith
LANGCHAIN_PROJECT=autonomous-cognitive-engine      # optional, LangSmith project name
```

> **Note:** The agent degrades gracefully without Tavily — sub-agents that rely on web search will return a fallback message. LangSmith tracing is optional.

---

## Milestones

---

### Milestone 1 — Structured Task Planning (Weeks 1–2)

**Goal:** Give the agent the ability to decompose any complex user request into a structured, ordered list of sub-tasks before executing anything.

#### What was built

The `write_todos` tool takes a high-level `objective` string and calls a JSON-mode LLM to produce exactly **5 ordered, actionable tasks**. Each task includes:
- `task` — a clear action-verb description (e.g., *"Research current trends in..."*)
- `status` — `"pending"` initially
- `result` — populated once the task is completed

The `plan_node` in `graph.py` calls `write_todos` directly (bypassing the LLM tool-call intermediary to avoid schema validation issues with Groq) and injects the result as a synthetic `AIMessage + ToolMessage` pair into the state. The `process_tool_results` node then parses the JSON response and stores the TODO list into `AgentState.todos`.

#### Task ordering rules enforced by the prompt

1. Research first
2. Analysis second
3. Design / Identify / Structure third
4. Write / Draft fourth
5. Review / Finalize fifth

#### Key files

- `tools.py` → `write_todos` tool (lines ~902–967)
- `graph.py` → `plan_node`, `process_tool_results` nodes

#### Example output

```json
[
  {"task": "Research background on X", "status": "pending", "result": ""},
  {"task": "Analyze key themes and trends", "status": "pending", "result": ""},
  {"task": "Identify evaluation criteria", "status": "pending", "result": ""},
  {"task": "Write a comprehensive report", "status": "pending", "result": ""},
  {"task": "Review and finalize the output", "status": "pending", "result": ""}
]
```

#### Evaluation

| Metric | Target |
|---|---|
| Task Decomposition Accuracy | > 80% of requests produce a logical, structured plan |
| Tool Invocation | `write_todos` invoked correctly in every run |
| State Storage | TODO list visible and correctly structured in LangSmith trace |

**Method:** Provide 5–10 varied complex requests and manually review the generated TODO lists. Use LangSmith to confirm correct tool invocation and state storage.

---

### Milestone 2 — Context Offloading via Virtual File System (Weeks 3–4)

**Goal:** Enable the agent to persist intermediate results across execution steps using a virtual file system, overcoming LLM context-window limitations.

#### What was built

A lightweight, in-memory virtual file system backed by a Python dictionary (`_file_system: dict[str, str]`). Four `@tool`-decorated functions expose it to the LLM:

| Tool | Signature | Purpose |
|---|---|---|
| `ls` | `ls()` | List all files |
| `read_file` | `read_file(filename)` | Load file content |
| `write_file` | `write_file(filename, content)` | Save content to a file |
| `edit_file` | `edit_file(filename, old_string, new_string)` | In-place string replacement |

The virtual file system is stored as `AgentState.files` (a `Dict[str, str]`) and is synced into and out of the global `_file_system` at the start of each node via `_set_files(state["files"])` and `_get_files()`.

#### File system conventions

Every task result is saved as `task_N_result.txt`. A compact summary (first 400 chars) is saved as `task_N_summary.txt` for reuse as context in subsequent tasks. The final synthesized report is saved as `FINAL_REPORT.txt`.

#### Final task read → modify → edit chain

The last task in every run is instructed to demonstrate the full file system dependency chain:
1. `read_file("task_N_result.txt")` — load the previous task's output
2. Generate a refined/combined version
3. `write_file("task_(N+1)_result.txt", combined_content)` — save the new result
4. `edit_file("task_(N+1)_result.txt", old_sentence, improved_sentence)` — refine in-place

This explicitly demonstrates the read → modify → edit workflow.

#### Key files

- `tools.py` → `ls`, `read_file`, `write_file`, `edit_file`, `_get_files`, `_set_files` (lines ~974–1021)
- `graph.py` → `reason_node`, `execute_node`, `update_task_node` — all sync the file system via `_set_files` / `_get_files`

#### Evaluation

| Metric | Target |
|---|---|
| Correct File System Tool Usage | > 80% of multi-step scenarios use write/read correctly |
| `edit_file` Demonstrated | At least once per run on the final task |
| State Persistence | File contents visible in `AgentState.files` in LangSmith trace |

**Method:** Create test scenarios that process information longer than the context window (e.g., summarize three long articles then combine). Inspect LangSmith traces for correct `write_file → read_file` sequences and verify file content in state updates.

---

### Milestone 3 — Sub-Agent Delegation (Weeks 5–6)

**Goal:** Allow the supervisor agent to route specialized sub-tasks to dedicated sub-agents, promoting modularity and context isolation.

#### What was built

A `task(agent_name, input_data)` delegation tool that dispatches to one of four specialist sub-agents registered in a `sub_agents` dictionary:

**Researcher** (`_researcher_agent`)
- Runs a Tavily web search (up to 4 results, `search_depth="advanced"`)
- Synthesizes results into structured research output with source citations
- Output format: Overview → Key facts → Recent developments → Considerations

**Analyst** (`_analyst_agent`)
- Runs a Tavily web search to gather current data
- Performs deep analysis on real-world results
- Output format: Main themes → Key patterns/trends → Critical observations → Actionable insights

**Summarizer** (`_summarizer_agent`)
- LLM-only; no web search
- Produces: one-sentence overview → 3–5 key points → one-sentence conclusion

**Writer** (`_writer_agent`)
- LLM-only; no web search
- Transforms raw notes/research into polished professional prose with headings and logical flow

#### Delegation routing logic

The `reason_node` classifies each task's description with keyword matching and injects explicit delegation guidance into the LLM prompt:

```python
needs_research  → task("researcher", topic)
needs_analysis  → task("analyst",    topic)
needs_writing   → task("writer",     raw_notes)
needs_summary   → task("summarizer", content)
handle_self     → LLM reasons directly, no delegation
```

#### Auto-save intercept

The `execute_node` intercepts sub-agent results and auto-saves the full content to `task_N_result.txt` when the LLM's own `write_file` call only saves a short label. This ensures the file system always contains the actual sub-agent output.

#### Sub-agent registry

```python
sub_agents: dict[str, callable] = {
    "summarizer": _summarizer_agent,   # LLM only
    "analyst":    _analyst_agent,      # Tavily + LLM
    "researcher": _researcher_agent,   # Tavily + LLM
    "writer":     _writer_agent,       # LLM only
}
```

#### Key files

- `tools.py` → `task` tool, `_researcher_agent`, `_analyst_agent`, `_summarizer_agent`, `_writer_agent`, `sub_agents` registry (lines ~1027–1164)
- `graph.py` → `reason_node` (delegation classification), `execute_node` (auto-save intercept)

#### Evaluation

| Metric | Target |
|---|---|
| Successful Delegation Rate | > 80% of relevant tasks correctly delegated |
| Result Integration | Sub-agent output saved to file system and used in subsequent tasks |
| LangSmith Trace | `[Milestone3] Delegated to sub-agent: <name>` visible in execution log |

**Method:** Design test cases where specific sub-tasks should be handled by a defined sub-agent (e.g., a research task → researcher agent). Verify in LangSmith that: the supervisor calls `task(...)` with the correct agent name, the sub-agent executes (Tavily search is visible for researcher/analyst), and the result is stored correctly in `task_N_result.txt`.

---

## Running the Agent

```bash
python run.py
```

You will see a startup banner and an input prompt:

```
╔══════════════════════════════════════════════════════════════════╗
║         AUTONOMOUS COGNITIVE ENGINE  —  Deep Research Agent      ║
╠══════════════════════════════════════════════════════════════════╣
║  Milestone 1 : Structured Planning   (write_todos)               ║
║  Milestone 2 : Virtual File System   (write / read / edit)       ║
║  Milestone 3 : Sub-Agent Delegation  (summarizer / analyst / ..) ║
╚══════════════════════════════════════════════════════════════════╝

Enter complex task:

>>>
```

**Example inputs:**
```
>>> Analyze the impact of generative AI on the software engineering job market
>>> Research recent advances in CRISPR gene editing and their clinical implications
>>> Compare cloud providers AWS, GCP, and Azure for enterprise ML workloads
```

Type `exit`, `quit`, or `q` to stop.

### Example session output

```
  Task : Analyze the impact of generative AI on software engineering

==================================================
 TASK PLAN CREATED
==================================================
[
  {"task": "Research current state of generative AI tools...", "status": "pending"},
  {"task": "Analyze impact on developer productivity...",      "status": "pending"},
  ...
]

⏳ Executing Task 1/5: Research current state of generative AI tools...
  🔀 Delegated → researcher
✅ Completed Task 1/5

⏳ Executing Task 2/5: Analyze impact on developer productivity...
  🔀 Delegated → analyst
✅ Completed Task 2/5
...

✅ Final report created

==================================================
 TASK PLAN COMPLETED
==================================================
...

==================================================
 MILESTONE 2  —  Virtual File System  (6 files)
==================================================
  - FINAL_REPORT.txt           (1842 chars)
  - task_1_result.txt          (953 chars)
  ...

==================================================
 MILESTONE 3  —  Sub-Agent Delegations
==================================================
  🔀 researcher
  🔀 analyst
  🔀 writer

==================================================
 FINAL REPORT
==================================================
...
```

---

## Agent Workflow

```
START
  │
  ▼
plan_node           ← calls write_todos directly; injects synthetic tool messages
  │
  ▼
process_tool_results ← parses TODO JSON; stores into AgentState.todos
  │
  ▼
select_task_node    ← finds next "pending" TODO; sets current_task_index
  │
  ├── (all done) ──▶ synthesize_node ──▶ END
  │
  ▼
reason_node         ← classifies task; builds prompt with delegation guidance
  │
  ├── (tool calls) ──▶ execute_node ──▶ update_task_node ──▶ select_task_node (loop)
  │
  └── (no tool calls) ──▶ update_task_node ──▶ select_task_node (loop)

synthesize_node     ← reads all task_N_result.txt files; generates FINAL_REPORT.txt
```

---

## Evaluation

| Milestone | Key Metric | Success Threshold |
|---|---|---|
| 1 — Planning | Task Decomposition Accuracy | > 80% of requests produce a logical 5-task plan |
| 2 — File System | Correct File System Tool Usage | > 80% of multi-step scenarios use read/write correctly |
| 3 — Delegation | Successful Delegation & Result Integration | > 80% of relevant test cases correctly delegate and integrate results |

All milestones use **LangSmith Tracing** as the primary verification tool. Enable it by setting `LANGCHAIN_TRACING_V2=true` and `LANGSMITH_API_KEY` in your `.env` file.
