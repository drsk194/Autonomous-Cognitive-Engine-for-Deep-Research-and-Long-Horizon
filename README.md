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
  - [Milestone 1 — Structured Task Planning](#milestone-1--structured-task-planning)
  - [Milestone 2 — Context Offloading via Virtual File System](#milestone-2--context-offloading-via-virtual-file-system)
  - [Milestone 3 — Sub-Agent Delegation](#milestone-3--sub-agent-delegation)
  - [Milestone 4 — Full Integration & Use Case Application](#milestone-4--full-integration--use-case-application)
- [Running the Agent](#running-the-agent)
- [API Reference](#api-reference)
- [Agent Workflow](#agent-workflow)
- [Evaluation](#evaluation)

---

## Project Overview

The **Autonomous Cognitive Engine** is a "Deep Cognitive Task Framework" that moves beyond simple tool-calling loops to support:

- **Structured planning** — breaks high-level objectives into ordered, actionable TODO lists
- **Smart query routing** — simple questions (e.g. "what is AI?") are answered directly without triggering the full pipeline
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
├── Simple query? (e.g. "what is AI?") ──→ Direct LLM answer (no pipeline)
│
└── Complex task?
          │
          ▼
     Memory Check ──── Hit ──→ Return cached report instantly (⚡)
          │ Miss
          ▼
┌─────────────────────────────────────────────────────┐
│                  LangGraph StateGraph               │
│                                                     │
│  ┌──────┐   ┌─────────┐   ┌─────────────┐           │
│  │ Plan │──▶│ Process │──▶│ Select Task│◀─────┐   │
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
│                         │  │  task()   │──┼──▶ Sub-Agents
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
| LLM Provider | Groq (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) |
| Web Search | Tavily API |
| API Layer | FastAPI |
| Frontend | React (JSX) |
| Observability | LangSmith |
| Package Manager | `uv` (recommended) or `pip` |
| Environment Variables | `python-dotenv` |

---

## Project Structure

```
deep-research_agent/
│
├── api.py            # FastAPI app — /run, /memory endpoints, CORS
├── graph.py          # LangGraph workflow — all nodes and graph assembly
├── state.py          # AgentState TypedDict — shared state definition
├── tools.py          # All tool definitions (planning, file system, sub-agents)
├── run.py            # CLI runner + simple query classifier + run_supervisor()
├── memory.py         # Persistent memory — save_memory() / search_memory()
├── eval.py           # Output evaluation — LLM-as-a-judge scoring (10 test cases)
│
├── frontendpage/
│   └── src/
│       └── App.js    # React UI — chat interface, history sidebar, theme toggle
│
├── memory.json       # Auto-generated persistent memory store
├── .env              # API keys (not committed)
└── README.md
```

### File Descriptions

**`state.py`** — Defines `AgentState`, the shared LangGraph state:
- `messages` — full conversation and tool call history
- `todos` — structured TODO list (`task`, `status`, `result`)
- `current_task_index` — index of the currently executing task (`None` when all done)
- `files` — virtual file system dictionary `{filename → content}`
- `execution_log` — human-readable trace of every major step
- `delegation_log` — record of every sub-agent delegation event

**`tools.py`** — All LangChain `@tool` definitions across all milestones:
- `write_todos` (Milestone 1)
- `ls`, `read_file`, `write_file`, `edit_file` (Milestone 2)
- `task`, plus `_researcher_agent`, `_analyst_agent`, `_summarizer_agent`, `_writer_agent` (Milestone 3)

**`graph.py`** — The full LangGraph `StateGraph`:
- Nodes: `plan`, `process`, `select_task`, `reason`, `execute`, `update_task`, `synthesize`
- Deterministic sub-agent routing via `_route_to_agent()`
- Conditional routing logic between nodes

**`run.py`** — CLI entry point and API runner:
- `_is_simple_query()` — classifies short/factual questions to bypass the pipeline
- `_direct_answer()` — answers simple questions with a single LLM call
- `run_agent()` — streams graph execution with live progress indicators
- `run_supervisor()` — invokes the graph synchronously for the FastAPI endpoint

**`api.py`** — FastAPI application (Milestone 4):
- `POST /run` — runs the agent, scores output, returns `report`, `score`, `from_memory`, `is_simple`
- `GET /memory` — returns all saved sessions for the frontend history sidebar

**`memory.py`** — Persistent cross-session memory:
- `save_memory(entry)` — appends `{topic, summary, todos, delegation_log}` to `memory.json`
- `search_memory(query)` — fuzzy keyword-matches against stored topics (35% overlap threshold)

**`eval.py`** — Output quality evaluation:
- Runs 10 test cases across all 4 milestones
- LLM-as-a-judge scoring (1–10) per report
- Pass/fail against 80% threshold for M1–M3, 70% for M4

**`frontendpage/src/App.js`** — React UI:
- Chat bubble interface (user right, agent left)
- Collapsible history sidebar with past sessions, task checklists, delegation logs
- System-default dark/light theme with manual toggle
- "⚡ Retrieved from past memory" badge on cached responses

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd deep-research_agent
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
pip install langgraph langchain langchain-groq langsmith \
            tavily-python fastapi uvicorn python-dotenv
```

### 4. Configure environment variables

Create a `.env` file in `deep-research_agent/`:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=autonomous_cognitive_engine
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

> **Note:** The agent degrades gracefully without Tavily — sub-agents that rely on web search return a fallback message. LangSmith tracing is optional.

### 5. Install frontend dependencies

```bash
cd frontendpage
npm install
```

---

## Milestones

---

### Milestone 1 — Structured Task Planning

**Goal:** Give the agent the ability to decompose any complex user request into a structured, ordered list of sub-tasks before executing anything.

#### What was built

The `write_todos` tool takes a high-level `objective` string and calls a JSON-mode LLM (`llama-3.3-70b-versatile`) to produce exactly **5 ordered, actionable tasks**. Each task includes:
- `task` — a clear action-verb description (e.g., *"Research current trends in..."*)
- `status` — `"pending"` initially
- `result` — populated once the task is completed

The `plan_node` in `graph.py` calls `write_todos` directly and injects the result as a synthetic `AIMessage + ToolMessage` pair into the state so LangSmith traces the tool call correctly. The `process_tool_results` node then parses the JSON and stores the TODO list into `AgentState.todos`.

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
  {"task": "Evaluate and finalize the output", "status": "pending", "result": ""}
]
```

#### Evaluation

| Metric | Target |
|---|---|
| Task Decomposition Accuracy | > 80% of requests produce a logical, structured plan |
| Tool Invocation | `write_todos` invoked correctly in every run |
| State Storage | TODO list visible and correctly structured in LangSmith trace |

---

### Milestone 2 — Context Offloading via Virtual File System

**Goal:** Enable the agent to persist intermediate results across execution steps using a virtual file system, overcoming LLM context-window limitations.

#### What was built

A lightweight, in-memory virtual file system backed by a Python dictionary (`_file_system: dict[str, str]`). Four `@tool`-decorated functions expose it to the LLM:

| Tool | Signature | Purpose |
|---|---|---|
| `ls` | `ls()` | List all files |
| `read_file` | `read_file(filename)` | Load file content |
| `write_file` | `write_file(filename, content)` | Save content to a file |
| `edit_file` | `edit_file(filename, old_string, new_string)` | In-place string replacement |

The virtual file system is stored as `AgentState.files` and synced into/out of the global `_file_system` at the start of each node via `_set_files()` and `_get_files()`.

#### File system conventions

Every task result is saved as `task_N_result.txt`. A compact summary (first 600 chars) is saved as `task_N_summary.txt` for context reuse in subsequent tasks. The final synthesized report is saved as `FINAL_REPORT.txt`.

#### Final task read → modify → edit chain

The last task in every run demonstrates the full file system dependency chain:
1. `read_file("task_N_result.txt")` — load the previous task's output
2. Generate a refined/combined version
3. `write_file("task_(N+1)_result.txt", combined_content)` — save the new result
4. `edit_file("task_(N+1)_result.txt", old_sentence, improved_sentence)` — refine in-place

#### Key files
- `tools.py` → `ls`, `read_file`, `write_file`, `edit_file`
- `graph.py` → `reason_node`, `execute_node`, `update_task_node`

#### Evaluation

| Metric | Target |
|---|---|
| Correct File System Tool Usage | > 80% of multi-step scenarios use write/read correctly |
| `edit_file` Demonstrated | At least once per run on the final task |
| State Persistence | File contents visible in `AgentState.files` in LangSmith trace |

---

### Milestone 3 — Sub-Agent Delegation

**Goal:** Allow the supervisor agent to route specialized sub-tasks to dedicated sub-agents, promoting modularity and context isolation.

#### What was built

A `task(agent_name, input_data)` delegation tool that dispatches to one of four specialist sub-agents. Routing is **deterministic Python** — no LLM compliance required:

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
- Produces: one-sentence overview → 4–6 key points → one-sentence conclusion

**Writer** (`_writer_agent`)
- LLM-only; no web search
- Transforms raw notes/research into polished professional prose with headings and logical flow

#### Delegation routing logic

The `_route_to_agent()` function in `graph.py` classifies each task by keyword matching:

```python
task index 0 or "research/find/gather/..."  → task("researcher", topic)
"analyze/compare/evaluate/assess/..."       → task("analyst",    topic)
"write/draft/compose/report/..."            → task("writer",     notes)
"summarize/condense/brief/..."              → task("summarizer", content)
default                                     → task("analyst",    topic)
```

Every delegation is recorded in `AgentState.delegation_log` and visible in LangSmith traces as `[Milestone3] Delegated to sub-agent: <name>`.

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
- `graph.py` → `_route_to_agent()`, `reason_node`

#### Evaluation

| Metric | Target |
|---|---|
| Successful Delegation Rate | > 80% of relevant tasks correctly delegated |
| Result Integration | Sub-agent output saved to file system and used in subsequent tasks |
| LangSmith Trace | `[Milestone3] Delegated to sub-agent: <name>` visible in every run |

---

### Milestone 4 — Full Integration & Use Case Application

**Goal:** Combine all prior components into a single cohesive system, expose it via a REST API, add a user interface, implement persistent memory, and validate end-to-end quality with automated evaluation.

#### What was built

**FastAPI Backend (`api.py`)**

```
POST /run     { "query": "..." }  →  { "report": "...", "score": "...", "from_memory": bool, "is_simple": bool }
GET  /memory                      →  [ { "topic", "summary", "todos", "delegation_log" }, ... ]
GET  /                            →  { "message": "Supervisor Agent API Running" }
```

**Smart Query Routing (`run.py`)**

Simple questions bypass the full pipeline entirely:

| Input | Behaviour |
|---|---|
| `what is AI?` | Direct LLM answer — no todos, no delegation |
| `explain machine learning` | Direct LLM answer |
| `Research AI impact in healthcare 2025` | Full pipeline |
| `Create a business plan for a startup` | Full pipeline |

**Persistent Memory (`memory.py`)**

Cross-session memory backed by `memory.json`:
- `save_memory(entry)` — stores `{topic, summary, todos, delegation_log}` after every run
- `search_memory(query)` — fuzzy keyword match (35% overlap threshold for retrieval, 55% for deduplication)
- Memory hit skips all LLM calls — instant cached response with **⚡ Retrieved from past memory** badge in UI

**Automated Evaluation (`eval.py`)**

- 10 test cases covering all 4 milestones
- LLM-as-a-judge scoring (1–10) per report
- Pass/fail summary against 80% threshold (M1–M3) and 70% threshold (M4)

**React Frontend (`frontendpage/src/App.js`)**

- Chat bubble UI — user messages right, agent responses left
- Collapsible history sidebar — all past sessions with task checklists and color-coded delegation logs
- "Load report →" button to reload any past session
- System-default dark/light theme with manual toggle (top-right)
- Animated typing dots while agent runs
- Quality score badge on each research response

#### Evaluation Results

| Milestone | Pass Rate | Threshold |
|---|---|---|
| M1 — Planning | **100%** | 80% |
| M2 — File System | **100%** | 80% |
| M3 — Delegation | **100%** | 80% |
| M4 — End-to-End | **100%** | 70% |

Average LLM-as-a-judge score: **8 / 10**

---

## Running the Agent

### Option 1 — React UI + FastAPI (Recommended)

**Terminal 1 — Backend:**
```bash
cd deep-research_agent
.venv/Scripts/python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd deep-research_agent/frontendpage
npm start
```

Open `http://localhost:3000`, enter a research query, and click **Send**.

### Option 2 — CLI

```bash
cd deep-research_agent
.venv/Scripts/python.exe run.py
```

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
>>> what is machine learning?
```

### Option 3 — Run Full Evaluation

```bash
cd deep-research_agent
.venv/Scripts/python.exe eval.py
```

### Example session output

```
Task : Analyze the impact of generative AI on software engineering

==================================================
 TASK PLAN CREATED
==================================================
[{"task": "Research current state of generative AI tools...", "status": "pending"},
 {"task": "Analyze impact on developer productivity...",      "status": "pending"},
 ...]

⏳ Executing Task 1/5: Research current state of generative AI tools...
  🔀 Delegated → researcher
✅ Completed Task 1/5
⏳ Executing Task 2/5: Analyze impact on developer productivity...
  🔀 Delegated → analyst
✅ Completed Task 2/5
...
✅ Final report created

==================================================
 MILESTONE 2  —  Virtual File System  (11 files)
==================================================
  - FINAL_REPORT.txt                             (3842 chars)
  - task_1_result.txt                            (2953 chars)
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
  "report": "**Executive Summary**\n\n...",
  "score": "8",
  "from_memory": false,
  "is_simple": false
}
```

### `GET /memory`
Returns all saved sessions (newest first).

**Response:**
```json
[
  {
    "topic": "Research AI in healthcare...",
    "summary": "**Executive Summary**...",
    "todos": [{"task": "...", "status": "completed", "result": "..."}],
    "delegation_log": ["Task 1 -> researcher: ...", "Task 2 -> analyst: ..."]
  }
]
```

---

## Agent Workflow

```
START
│
▼
plan_node            ← calls write_todos; injects synthetic tool messages for LangSmith
│
▼
process_tool_results ← parses TODO JSON; enforces 4–6 task count; stores into AgentState.todos
│
▼
select_task_node     ← finds next "pending" TODO; sets current_task_index
│
├── (all done) ──▶ synthesize_node ──▶ save_memory() ──▶ END
│
▼
reason_node          ← _route_to_agent() picks sub-agent; calls sub_agents[agent](input)
                       injects AIMessage + ToolMessage for LangSmith trace
│
▼
update_task_node     ← marks task completed; writes compact summary file
│
└──▶ select_task_node (loop)

synthesize_node      ← reads all task_N_result.txt files; LLM generates FINAL_REPORT.txt;
                       saves run to memory.json
```

---

## Evaluation

| Milestone | Key Metric | Success Threshold |
|---|---|---|
| 1 — Planning | Task Decomposition Accuracy | > 80% of requests produce a logical 5-task plan |
| 2 — File System | Correct File System Tool Usage | > 80% of multi-step scenarios use read/write correctly |
| 3 — Delegation | Successful Delegation & Result Integration | > 80% of relevant test cases correctly delegate |
| 4 — Full Integration | End-to-End Completion Rate & Output Quality | > 70% completion; output rated ≥ 7/10 |

All milestones use **LangSmith Tracing** as the primary verification tool. Enable it by setting `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` in your `.env` file.

---

## Author

**Sasi Kannan** — Autonomous Cognitive Engine for Deep Research and Long-Horizon Tasks
