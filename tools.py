"""
tools.py — All tool definitions for the Autonomous Cognitive Engine.

Milestone 1 : write_todos        — LLM-powered strict JSON task decomposition (exactly 5 steps)
Milestone 2 : ls, read_file, write_file, edit_file — virtual file system
Milestone 3 : task               — sub-agent delegation
              researcher         — Tavily web search + LLM synthesis
              analyst            — Tavily web search + LLM analysis
              summarizer         — LLM-only summarization
              writer             — LLM-only polished writing
"""
from __future__ import annotations
import json, os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

# ── API keys ──────────────────────────────────────────────────────────────────
_groq_api_key   = os.getenv("GROQ_API_KEY", "")
_tavily_api_key = os.getenv("TAVILY_API_KEY", "")

# ── LLM instances ─────────────────────────────────────────────────────────────
# JSON-mode LLM — strict structured output for write_todos
_llm_json = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=_groq_api_key,
    model_kwargs={"response_format": {"type": "json_object"}},
    max_tokens=1024,
)

# Plain LLM — sub-agents (higher token budget for real content)
_llm_plain = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=_groq_api_key,
    max_tokens=1500,
)


# ── Tavily web search ─────────────────────────────────────────────────────────
def _tavily_search(query: str, max_results: int = 4) -> str:
    """Run a Tavily web search and return clean formatted results."""
    if not _tavily_api_key:
        return f"[Tavily not configured] No web results for: {query}"
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=_tavily_api_key)
        response = client.search(query=query, max_results=max_results, search_depth="advanced")
        results = response.get("results", [])
        if not results:
            return f"No web results found for: {query}"
        formatted = []
        for i, r in enumerate(results, 1):
            title   = r.get("title", "No title")
            url     = r.get("url", "")
            content = r.get("content", "")[:600]
            formatted.append(f"[Source {i}] {title}\n    URL: {url}\n    {content}")
        return "\n\n".join(formatted)
    except ImportError:
        return "[tavily-python not installed]  Run: pip install tavily-python"
    except Exception as exc:
        return f"[Tavily error] {str(exc)[:200]}"


# ============================================================================
# MILESTONE 1 — write_todos: LLM-powered strict JSON task decomposition
# ============================================================================

# Strict planning prompt — enforces action verbs, 5 steps, no duplicates
_PLANNING_SYSTEM = """You are a senior project planning assistant.
Your ONLY job is to decompose an objective into EXACTLY 5 structured TODO tasks.

STRICT RULES — violating any rule is unacceptable:
1. Return ONLY valid JSON — no markdown fences, no explanation, no extra text.
2. The JSON must have exactly one key: "todos" containing a list of exactly 5 objects.
3. Each object must have exactly these keys: "task", "status", "result".
4. "status" must always be "pending". "result" must always be "".
5. Each "task" value MUST begin with one of these action verbs (case-sensitive first word):
   Research | Analyze | Identify | Design | Write | Compare | Evaluate | Gather | Investigate | Assess
6. Tasks must follow this logical order:
   Step 1 → Research/Gather (collect raw information)
   Step 2 → Analyze/Compare (process the information)
   Step 3 → Identify/Assess (extract insights)
   Step 4 → Write/Design (produce structured output)
   Step 5 → Evaluate/Finalize (review and recommend)
7. Tasks must be NON-OVERLAPPING and NON-REDUNDANT — no two tasks should do the same thing.
8. Each task must be SPECIFIC to the given objective — no generic filler tasks.
9. Do NOT repeat the same action verb across tasks.

Required output format (return exactly this, nothing else):
{"todos": [{"task": "Research ...", "status": "pending", "result": ""}, {"task": "Analyze ...", "status": "pending", "result": ""}, {"task": "Identify ...", "status": "pending", "result": ""}, {"task": "Write ...", "status": "pending", "result": ""}, {"task": "Evaluate ...", "status": "pending", "result": ""}]}"""


@tool
def write_todos(objective: str) -> dict:
    """
    Decompose a complex objective into EXACTLY 5 actionable TODO tasks using the LLM.
    Returns structured JSON: {"todos": [{"task": "...", "status": "pending", "result": ""}]}

    This tool MUST be called first for every complex request. Never skip planning.
    """
    user_prompt = f"OBJECTIVE: {objective}\n\nDecompose into exactly 5 structured TODO tasks now:"

    try:
        response = _llm_json.invoke([
            SystemMessage(content=_PLANNING_SYSTEM),
            HumanMessage(content=user_prompt),
        ])
        content = response.content.strip()

        # Strip any accidental markdown fences
        if content.startswith("```json"):
            content = content.split("```json", 1)[1].split("```", 1)[0].strip()
        elif content.startswith("```"):
            content = content.split("```", 1)[1].split("```", 1)[0].strip()

        data = json.loads(content)

        if "todos" not in data or not isinstance(data["todos"], list):
            raise ValueError("Missing 'todos' key in LLM response")

        normalised = []
        for item in data["todos"]:
            task_text = item.get("task", "").strip()
            if not task_text:
                continue
            normalised.append({
                "task":   task_text,
                "status": "pending",
                "result": "",
            })

        # Enforce exactly 5
        action_verbs = ["Research", "Analyze", "Identify", "Write", "Evaluate"]
        while len(normalised) < 5:
            verb = action_verbs[len(normalised)]
            normalised.append({
                "task":   f"{verb} and finalize findings for: {objective}",
                "status": "pending",
                "result": "",
            })

        return {"todos": normalised[:5]}

    except Exception as exc:
        # Structured fallback — always 5 tasks, always action verbs, always specific
        return {
            "todos": [
                {"task": f"Research background information and current state of: {objective}",       "status": "pending", "result": ""},
                {"task": f"Analyze key components, trends, and challenges in: {objective}",          "status": "pending", "result": ""},
                {"task": f"Identify critical insights, gaps, and opportunities within: {objective}", "status": "pending", "result": ""},
                {"task": f"Write a comprehensive structured report covering: {objective}",           "status": "pending", "result": ""},
                {"task": f"Evaluate findings and provide actionable recommendations for: {objective}", "status": "pending", "result": ""},
            ]
        }


# ============================================================================
# MILESTONE 2 — Virtual File System
# ============================================================================

_file_system: dict[str, str] = {}


def _get_files() -> dict[str, str]:
    return _file_system.copy()


def _set_files(files: dict[str, str]) -> None:
    global _file_system
    _file_system = files.copy() if files else {}


@tool
def ls() -> str:
    """List all files in the virtual file system."""
    files = sorted(_file_system.keys())
    if not files:
        return "Virtual file system is empty."
    return "Files:\n" + "\n".join(f"  - {f}" for f in files)


@tool
def read_file(filename: str) -> str:
    """Read content from a file in the virtual file system."""
    if filename not in _file_system:
        available = ", ".join(sorted(_file_system.keys())) or "none"
        return f"Error: File '{filename}' not found. Available: {available}"
    return _file_system[filename]


@tool
def write_file(filename: str, content: str) -> str:
    """Write content to the virtual file system. Content must be real output — never a placeholder."""
    _file_system[filename] = content
    return f"Wrote {len(content)} characters to '{filename}'."


@tool
def edit_file(filename: str, old_string: str, new_string: str) -> str:
    """Replace the first occurrence of old_string with new_string in an existing file."""
    if filename not in _file_system:
        return f"Error: File '{filename}' not found."
    content = _file_system[filename]
    if old_string not in content:
        return f"Error: String not found in '{filename}'. Cannot edit."
    _file_system[filename] = content.replace(old_string, new_string, 1)
    return f"Edited '{filename}' successfully."


# ============================================================================
# MILESTONE 3 — Sub-agent implementations
# ============================================================================

def _researcher_agent(input_text: str) -> str:
    """Researcher: Tavily web search + LLM synthesis."""
    print(f"    [Tavily] researcher → {input_text[:70]}...")
    search_results = _tavily_search(input_text, max_results=4)
    system = (
        "You are a specialized research agent with real-time web search results. "
        "Synthesize findings into structured research output:\n"
        "  - Overview (2-3 sentences)\n"
        "  - Key facts from sources (bullet points, cite [Source N])\n"
        "  - Recent developments\n"
        "  - Important considerations\n"
        "Be factual, detailed, cite sources. Minimum 300 words."
    )
    prompt = f"Research topic: {input_text}\n\nWeb search results:\n{search_results}\n\nSynthesize:"
    response = _llm_plain.invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    return response.content


def _analyst_agent(input_text: str) -> str:
    """Analyst: Tavily web search + deep LLM analysis."""
    print(f"    [Tavily] analyst → {input_text[:70]}...")
    search_results = _tavily_search(input_text, max_results=4)
    system = (
        "You are a specialized analysis agent with real-time web search results. "
        "Perform deep analysis and extract actionable insights:\n"
        "  - Main themes identified\n"
        "  - Key patterns or trends (cite [Source N])\n"
        "  - Critical observations\n"
        "  - Actionable insights and implications\n"
        "Be analytical and thorough. Minimum 300 words."
    )
    prompt = f"Analysis topic: {input_text}\n\nWeb search results:\n{search_results}\n\nAnalyze:"
    response = _llm_plain.invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    return response.content


def _summarizer_agent(input_text: str) -> str:
    """Summarizer: LLM-only, condenses content into structured summary."""
    system = (
        "You are a specialized summarization agent. "
        "Produce a clear structured summary: "
        "one-sentence overview, 4-6 key points with details, one-sentence conclusion. "
        "Minimum 150 words."
    )
    response = _llm_plain.invoke([
        SystemMessage(content=system),
        HumanMessage(content=f"Summarize the following:\n\n{input_text}"),
    ])
    return response.content


def _writer_agent(input_text: str) -> str:
    """Writer: LLM-only, transforms raw notes into polished professional content."""
    system = (
        "You are a specialized writing agent. "
        "Transform raw information into clear, professional written content "
        "with appropriate headings, logical flow, and precise language. "
        "Minimum 300 words."
    )
    response = _llm_plain.invoke([
        SystemMessage(content=system),
        HumanMessage(content=f"Transform into polished written output:\n\n{input_text}"),
    ])
    return response.content


# ── Sub-agent registry ────────────────────────────────────────────────────────
sub_agents: dict[str, callable] = {
    "researcher": _researcher_agent,   # Tavily + LLM
    "analyst":    _analyst_agent,      # Tavily + LLM
    "summarizer": _summarizer_agent,   # LLM only
    "writer":     _writer_agent,       # LLM only
}


# ============================================================================
# MILESTONE 3 — Delegation tool
# ============================================================================

@tool
def task(agent_name: str, input_data: str) -> str:
    """
    Delegate a sub-task to a specialized sub-agent and return its output.

    Available agents:
      - "researcher" : Searches the web (Tavily) + synthesizes findings. Use for: research/find/gather/investigate/latest/current
      - "analyst"    : Searches the web (Tavily) + performs deep analysis. Use for: analyze/compare/evaluate/assess/impact
      - "summarizer" : Summarizes provided content (no web search). Use for: summarize/condense/brief
      - "writer"     : Converts raw notes into polished written content. Use for: write/draft/compose/report/finalize

    After calling this tool, ALWAYS call write_file to store the result.

    Args:
        agent_name : One of: researcher, analyst, summarizer, writer
        input_data : Specific topic or content to pass to the sub-agent
    """
    if agent_name not in sub_agents:
        available = ", ".join(sub_agents.keys())
        return f"Error: Agent '{agent_name}' not found. Available: {available}"
    return sub_agents[agent_name](input_data)
