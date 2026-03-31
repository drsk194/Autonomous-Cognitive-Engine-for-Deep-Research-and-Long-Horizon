# Autonomous Cognitive Engine — Deep Research Agent

> **Enabling Long-Horizon Tasks with Memory, Planning, and Multi-Agent Collaboration**

A sophisticated, autonomous AI agent framework built with **LangGraph** that executes complex, multi-step research and reasoning tasks. The agent decomposes high-level objectives into structured plans, offloads context to a virtual file system, delegates specialized sub-tasks to purpose-built sub-agents, and exposes everything through a REST API with a React frontend.

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
  - [Milestone 4 — Full Integration & Use Case Application](#milestone-4--full-integration--use-case-application-weeks-78)
- [Running the Agent](#running-the-agent)
- [API Reference](#api-reference)
- [Agent Workflow](#agent-workflow)
- [Evaluation](#evaluation)

---

## Project Overview

The **Autonomous Cognitive Engine** is a "Deep Cognitive Task Framework" that moves beyond simple tool-calling loops to support:

- **Structured planning** — breaks high-level objectives into ordered, actionable TODO lists
- **Context offloading** — stores intermediate results in a virtual file system to overcome LLM context-window limits
- **Sub-agent delegation** — routes specialized sub-tasks (research, analysis, summarization, writing) to dedicated agents
- **Persistent memory** — saves completed research summaries to disk and surfaces relevant past runs on new requests
- **Stateful orchestration** — the entire workflow is managed as a LangGraph `StateGraph` with robust state tracking
- **REST API + UI** — a FastAPI backend and React frontend allow direct user interaction with the agent

---

## Architecture

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                  LangGraph StateGraph               │
│                                                     │
│  ┌──────┐   ┌─────────┐   ┌─────────────┐           │
│  │ Plan │──▶│ Process │──▶│ Select Task │◀────┐   │
│  └──────┘   └─────────┘   └──────┬──────┘       │   │
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
│                                  │ (all done)       │
│                         ┌────────▼────────┐         │
│                         │   Synthesize    │         │
│                         └────────┬────────┘         │
└──────────────────────────────────┼─────────────────┘
                                   ▼
                            Final Report + Score
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
| API Layer | FastAPI |
| Frontend | React (JSX) |
| Observability | LangSmith |
| Package Manager | `uv` (recommended) or `pip` |
| Environment Variables | `python-dotenv` |

---

## Project Structure

```
autonomous-cognitive-engine/
│
├── main.py           # FastAPI app — /run endpoint, CORS, evaluation
├── graph.py          # LangGraph workflow — all nodes and graph assembly
├── state.py          # AgentState TypedDict — shared state definition
├── tools.py          # All tool definitions (planning, file system, sub-agents)
├── run.py            # CLI runner + run_supervisor() used by the API
├── memory.py         # Persistent memory — save_memory() / search_memory()
├── eval.py           # Output evaluation — LLM-as-a-judge scoring
│
├── frontend/
│   └── App.jsx       # React UI — query input, report display, score display
│
├── memory.json       # Auto-generated persistent memory store
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

**`tools.py`** — All LangChain `@tool` definitions across all milestones:
- `write_todos` (Milestone 1)
- `ls`, `read_file`, `write_file`, `edit_file` (Milestone 2)
- `task`, plus `_researcher_agent`, `_analyst_agent`, `_summarizer_agent`, `_writer_agent` (Milestone 3)

**`graph.py`** — The full LangGraph `StateGraph`:
- Nodes: `plan`, `process`, `select_task`, `reason`, `execute`, `update_task`, `synthesize`
- Conditional routing logic between nodes
- System prompts for the execution and synthesis LLMs

**`run.py`** — CLI entry point and API runner:
- `run_agent()` — streams graph execution with live progress indicators for CLI use
- `run_supervisor()` — invokes the graph synchronously and returns `FINAL_REPORT.txt` for the FastAPI endpoint

**`main.py`** — FastAPI application (Milestone 4):
- `POST /run` — accepts a `query`, runs `run_supervisor()`, scores the output with `evaluate_output()`, and returns both

**`memory.py`** — Persistent cross-session memory (Milestone 4):
- `save_memory(entry)` — appends a `{topic, summary}` entry to `memory.json` (deduplicates by topic)
- `search_memory(query)` — keyword-matches against stored topics and returns relevant past runs

**`eval.py`** — Output quality evaluation (Milestone 4):
- Scores the final report using an LLM-as-a-judge approach

**`frontend/App.jsx`** — React UI (Milestone 4):
- Text area for entering the research query
- Calls `POST http://127.0.0.1:8000/run` and displays the final report and quality score

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
fastapi
uvicorn
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

- `tools.py` → `write_todos` tool
- `graph.py` → `plan_node`, `process_tool_results` nodes

#### Example output

```json
[
  {"task": "Research background on X",        "status": "pending", "result": ""},
  {"task": "Analyze key themes and trends",    "status": "pending", "result": ""},
  {"task": "Identify evaluation criteria",     "status": "pending", "result": ""},
  {"task": "Write a comprehensive report",     "status": "pending", "result": ""},
  {"task": "Review and finalize the output",   "status": "pending", "result": ""}
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

#### Key files

- `tools.py` → `ls`, `read_file`, `write_file`, `edit_file`, `_get_files`, `_set_files`
- `graph.py` → `reason_node`, `execute_node`, `update_task_node`

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

- `tools.py` → `task` tool, all four sub-agent functions, `sub_agents` registry
- `graph.py` → `reason_node` (delegation classification), `execute_node` (auto-save intercept)

#### Evaluation

| Metric | Target |
|---|---|
| Successful Delegation Rate | > 80% of relevant tasks correctly delegated |
| Result Integration | Sub-agent output saved to file system and used in subsequent tasks |
| LangSmith Trace | `[Milestone3] Delegated to sub-agent: <name>` visible in execution log |

**Method:** Design test cases where specific sub-tasks should be handled by a defined sub-agent. Verify in LangSmith that the supervisor calls `task(...)` with the correct agent name, the sub-agent executes, and the result is stored correctly in `task_N_result.txt`.

---

### Milestone 4 — Full Integration & Use Case Application (Weeks 7–8)

**Goal:** Combine all prior components into a single cohesive system, expose it via a REST API, add a user interface, implement persistent memory, and validate end-to-end quality with automated evaluation.

#### What was built

**FastAPI Backend (`main.py`)**

A production-ready REST API wrapping the full agent:

```
POST /run   { "query": "..." }  →  { "report": "...", "score": "..." }
GET  /      →  { "message": "Supervisor Agent API Running" }
```

CORS is configured to allow all origins, enabling the React frontend to connect freely during development.

**`run_supervisor()` (`run.py`)**

A synchronous graph runner used by the API. It invokes `graph.invoke(state)` with a fresh initial state, extracts `FINAL_REPORT.txt` from the final files dict, and returns it as a plain string.

**Persistent Memory (`memory.py`)**

Cross-session memory backed by `memory.json`:
- `save_memory(entry)` — called in `synthesize_node` after every successful run; stores `{topic, summary}` (deduplicates by topic)
- `search_memory(query)` — called in `plan_node` before task decomposition; keyword-matches the user's objective against stored topics and injects matching past summaries into the execution log for context reuse

**Automated Evaluation (`eval.py`)**

LLM-as-a-judge scoring: `evaluate_output(report)` assesses the final report and returns a quality score. The score is returned alongside the report in the API response so users can gauge output quality immediately.

**React Frontend (`frontend/App.jsx`)**

A functional UI with:
- A textarea for entering the research query
- A **Run Agent** button that calls `POST http://127.0.0.1:8000/run`
- A loading indicator while the agent executes
- Display of the quality score and the full formatted report

#### Key files

- `main.py` — FastAPI app, CORS, `/run` endpoint
- `run.py` — `run_supervisor()` for API use
- `memory.py` — `save_memory()`, `search_memory()`
- `eval.py` — `evaluate_output()`
- `frontend/App.jsx` — React UI

#### Evaluation

| Metric | Target |
|---|---|
| End-to-End Task Completion Rate | > 70% of complex tasks complete without critical errors |
| Output Quality | Final report rated "good" or "excellent" by LLM-as-a-judge |
| API Availability | `/run` endpoint returns correct `report` and `score` fields |
| Memory Reuse | Past run summaries surfaced and logged when topic overlaps |

**Method:** Run the fully integrated agent on 10–20 complex end-to-end queries via the API and UI. Use LangSmith to debug full runs and the `score` field in the API response to track output quality trends.

---

## Running the Agent

### Option 1 — React UI + FastAPI (Recommended)

Start the backend:
```bash
uvicorn main:app --reload
# API running at http://127.0.0.1:8000
```

Start the frontend:
```bash
cd frontend
npm install
npm start
# UI running at http://localhost:3000
```

Open `http://localhost:3000`, enter a research query, and click **Run Agent**.

### Option 2 — CLI

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

## API Reference

### `GET /`

Health check.

**Response:**
```json
{ "message": "Supervisor Agent API Running" }
```

### `POST /run`

Run the full agent pipeline on a query.

**Request body:**
```json
{ "query": "Your complex research query here" }
```

**Response:**
```json
{
  "report": "=== Section 1 ===\nTask: Research...\n\n...",
  "score":  "8/10"
}
```

---

## Agent Workflow

```
START
  │
  ▼
plan_node            ← searches memory for past runs; calls write_todos directly;
  │                    injects synthetic tool messages
  ▼
process_tool_results ← parses TODO JSON; enforces 4–6 task count; stores into AgentState.todos
  │
  ▼
select_task_node     ← finds next "pending" TODO; sets current_task_index
  │
  ├── (all done) ──▶ synthesize_node ──▶ save_memory() ──▶ END
  │
  ▼
reason_node          ← classifies task; builds prompt with delegation guidance + prior context
  │
  ├── (tool calls) ──▶ execute_node ──▶ update_task_node ──▶ select_task_node (loop)
  │
  └── (no tool calls) ──▶ update_task_node ──▶ select_task_node (loop)

synthesize_node      ← assembles all task_N_result.txt files; generates FINAL_REPORT.txt;
                       saves run to memory.json
```

---

## Evaluation

| Milestone | Key Metric | Success Threshold |
|---|---|---|
| 1 — Planning | Task Decomposition Accuracy | > 80% of requests produce a logical 5-task plan |
| 2 — File System | Correct File System Tool Usage | > 80% of multi-step scenarios use read/write correctly |
| 3 — Delegation | Successful Delegation & Result Integration | > 80% of relevant test cases correctly delegate and integrate results |
| 4 — Full Integration | End-to-End Completion Rate & Output Quality | > 70% completion rate; output rated "good" or "excellent" |

All milestones use **LangSmith Tracing** as the primary verification tool. Enable it by setting `LANGCHAIN_TRACING_V2=true` and `LANGSMITH_API_KEY` in your `.env` file.
