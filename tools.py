"""
tools.py
All tool definitions for the Autonomous Cognitive Engine.

Milestone 1 : write_todos        — LLM-powered task decomposition
Milestone 2 : ls, read_file, write_file, edit_file — virtual file system
Milestone 3 : task               — sub-agent delegation tool
              researcher         — Tavily web search + LLM synthesis
              analyst            — Tavily web search + LLM analysis
              summarizer         — LLM-only summarization
              writer             — LLM-only polished writing"""

from __future__ import annotations

import json
import os
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ===========================================================================
# Tavily web search helper
# ===========================================================================

_tavily_api_key = os.getenv("TAVILY_API_KEY", "")


def _tavily_search(query: str, max_results: int = 4) -> str:
    """
    Run a Tavily web search and return clean formatted results.
    Falls back gracefully if Tavily is unavailable or not configured.
    """
    if not _tavily_api_key:
        return f"[Tavily not configured] No web results for: {query}"
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=_tavily_api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )
        results = response.get("results", [])
        if not results:
            return f"No web results found for: {query}"

        formatted = []
        for i, r in enumerate(results, 1):
            title   = r.get("title", "No title")
            url     = r.get("url", "")
            content = r.get("content", "")[:500]
            formatted.append(
                f"[Source {i}] {title}\n"
                f"    URL: {url}\n"
                f"    {content}"
            )
        return "\n\n".join(formatted)

    except ImportError:
        return "[tavily-python not installed]  Run: pip install tavily-python"
    except Exception as exc:
        return f"[Tavily error] {str(exc)[:200]}"


# ===========================================================================
# Shared LLM instances
# ===========================================================================

_groq_api_key = os.getenv("GROQ_API_KEY", "")

# JSON-mode LLM — used only by write_todos
_llm_json = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=_groq_api_key,
    model_kwargs={"response_format": {"type": "json_object"}},
)

# Plain LLM — used by all sub-agents
_llm_plain = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=_groq_api_key,
    max_tokens=500,
)


# ===========================================================================
# MILESTONE 1 — Planning tool
# ===========================================================================

@tool
def write_todos(objective: str) -> dict:
    """
    Decompose a complex objective into 4-6 actionable TODO tasks.
    Returns structured JSON: {"todos": [{"task": "...", "status": "pending", "result": ""}]}
    """
    prompt = f"""You are a project planning assistant.
Break down the following objective into EXACTLY 5 clear, actionable tasks — no more, no less.

Rules:
- Each task MUST start with a strong action verb: Research, Analyze, Identify, Design, Write, Compare, Evaluate, Gather
- Tasks must be logically ordered: research first, analysis second, design/identify third, write fourth, review/finalize fifth
- Tasks must be non-overlapping and non-redundant
- Return ONLY valid JSON — no markdown, no extra text

OBJECTIVE: {objective}

Required JSON format:
{{
  "todos": [
    {{"task": "Task description here", "status": "pending", "result": ""}},
    {{"task": "Task description here", "status": "pending", "result": ""}}
  ]
}}"""

    try:
        response = _llm_json.invoke(prompt)
        content = response.content.strip()

        if content.startswith("```json"):
            content = content.split("```json", 1)[1].split("```", 1)[0].strip()
        elif content.startswith("```"):
            content = content.split("```", 1)[1].split("```", 1)[0].strip()

        data = json.loads(content)

        if "todos" not in data or not isinstance(data["todos"], list):
            raise ValueError("Missing or invalid 'todos' key")

        normalised = []
        for item in data["todos"]:
            normalised.append({
                "task":   item.get("task", "Unnamed task"),
                "status": item.get("status", "pending"),
                "result": item.get("result", ""),
            })

        # Enforce exactly 5 tasks
        while len(normalised) < 5:
            normalised.append({
                "task": f"Review and finalize the output for: {objective}",
                "status": "pending",
                "result": "",
            })

        return {"todos": normalised[:5]}

    except Exception as exc:
        return {
            "todos": [
                {"task": f"Research background information on: {objective}", "status": "pending", "result": ""},
                {"task": f"Analyze key aspects of: {objective}",            "status": "pending", "result": ""},
                {"task": f"Synthesize findings for: {objective}",           "status": "pending", "result": ""},
                {"task": f"Write final output for: {objective}",            "status": "pending", "result": ""},
            ]
        }


# ===========================================================================
# MILESTONE 2 — Virtual File System tools
# ===========================================================================

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
    """Write content to the virtual file system."""
    _file_system[filename] = content
    return f"Wrote {len(content)} characters to '{filename}'."


@tool
def edit_file(filename: str, old_string: str, new_string: str) -> str:
    """Replace the first occurrence of old_string with new_string in an existing file."""
    if filename not in _file_system:
        return f"Error: File '{filename}' not found."
    content = _file_system[filename]
    if old_string not in content:
        return f"Error: The string was not found in '{filename}'."
    _file_system[filename] = content.replace(old_string, new_string, 1)
    return f"Edited '{filename}' successfully."


# ===========================================================================
# MILESTONE 3 — Sub-Agent implementations
# ===========================================================================

def _researcher_agent(input_text: str) -> str:
    """
    Researcher sub-agent — powered by Tavily web search.

    Workflow:
      1. Search the web via Tavily for real-time results
      2. LLM synthesizes those results into structured research output
    """
    print(f"    [Tavily] researcher searching: {input_text[:60]}...")
    search_results = _tavily_search(input_text, max_results=4)

    system = (
        "You are a specialized research agent with access to real-time web search results. "
        "Your job is to synthesize web search results into clear, structured research. "
        "Structure your output with:\n"
        "  - Overview (2-3 sentences)\n"
        "  - Key facts from sources (bullet points with source numbers)\n"
        "  - Recent developments\n"
        "  - Important considerations\n"
        "Be factual. Cite [Source N] where relevant."
    )
    prompt = f"""Research topic: {input_text}

Web search results:
{search_results}

Synthesize the above into comprehensive, well-structured research:"""

    response = _llm_plain.invoke(
        [SystemMessage(content=system), HumanMessage(content=prompt)]
    )
    return response.content


def _analyst_agent(input_text: str) -> str:
    """
    Analyst sub-agent — powered by Tavily web search.

    Workflow:
      1. Search the web via Tavily to gather current data/context
      2. LLM performs deep analysis on the real-world search results
    """
    print(f"    [Tavily] analyst searching: {input_text[:60]}...")
    search_results = _tavily_search(input_text, max_results=4)

    system = (
        "You are a specialized analysis agent with access to real-time web search results. "
        "Your job is to analyze the search results and extract deep insights. "
        "Structure your analysis with:\n"
        "  - Main themes identified\n"
        "  - Key patterns or trends (with source references)\n"
        "  - Critical observations\n"
        "  - Actionable insights and implications\n"
        "Be analytical. Reference [Source N] to support your points."
    )
    prompt = f"""Analysis topic: {input_text}

Web search results:
{search_results}

Perform deep analysis of the above results:"""

    response = _llm_plain.invoke(
        [SystemMessage(content=system), HumanMessage(content=prompt)]
    )
    return response.content


def _summarizer_agent(input_text: str) -> str:
    """
    Summarizer sub-agent — LLM only (no web search needed, summarizes given content).
    """
    system = (
        "You are a specialized summarization agent. "
        "Produce a clear, concise summary structured as: "
        "one-sentence overview, 3-5 key points, one-sentence conclusion."
    )
    response = _llm_plain.invoke(
        [SystemMessage(content=system),
         HumanMessage(content=f"Summarize:\n\n{input_text}")]
    )
    return response.content


def _writer_agent(input_text: str) -> str:
    """
    Writer sub-agent — LLM only (no web search, polishes raw notes into final content).
    """
    system = (
        "You are a specialized writing agent. "
        "Transform raw information into clear, professional written content "
        "with appropriate headings, logical flow, and precise language."
    )
    response = _llm_plain.invoke(
        [SystemMessage(content=system),
         HumanMessage(content=f"Transform into polished written output:\n\n{input_text}")]
    )
    return response.content


# ===========================================================================
# Sub-agent registry
# ===========================================================================

sub_agents: dict[str, callable] = {
    "summarizer": _summarizer_agent,   # LLM only
    "analyst":    _analyst_agent,      # Tavily + LLM
    "researcher": _researcher_agent,   # Tavily + LLM
    "writer":     _writer_agent,       # LLM only
}


# ===========================================================================
# MILESTONE 3 — Delegation tool
# ===========================================================================

@tool
def task(agent_name: str, input_data: str) -> str:
    """
    Delegate a sub-task to a specialized sub-agent.

    Available agents:
      - "researcher" : Searches the web (Tavily) + synthesizes findings.
      - "analyst"    : Searches the web (Tavily) + performs deep analysis.
      - "summarizer" : Summarizes provided content (no web search).
      - "writer"     : Converts raw notes into polished written content.

    Args:
        agent_name : Name of the sub-agent to invoke.
        input_data : Topic or content to pass to the sub-agent.
    """
    if agent_name not in sub_agents:
        available = ", ".join(sub_agents.keys())
        return f"Error: Agent '{agent_name}' not found. Available: {available}"

    agent_fn = sub_agents[agent_name]
    result   = agent_fn(input_data)
    return result
    
