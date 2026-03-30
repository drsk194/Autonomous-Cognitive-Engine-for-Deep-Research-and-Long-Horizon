"""
state.py — Shared state for the Autonomous Cognitive Engine.
Milestones 1-4: planning, file system, sub-agent delegation, full integration.
"""
from __future__ import annotations
from typing import Annotated, Dict, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(dict):
    """
    LangGraph shared state.

    messages           : Conversation + tool call history (add_messages reducer).
    todos              : Structured TODO list from write_todos [{task, status, result}].
    current_task_index : Active TODO index (None = all done).
    files              : Virtual file system {filename: content}.
    execution_log      : Step-by-step trace of every node action.
    delegation_log     : Record of every sub-agent delegation event (Milestone 3/4).
    final_report       : Synthesized final report string.
    """
    # TypedDict-style annotations for LangGraph
    messages:            Annotated[List[BaseMessage], add_messages]
    todos:               List[dict]
    current_task_index:  Optional[int]
    files:               Dict[str, str]
    execution_log:       List[str]
    delegation_log:      List[str]
    final_report:        Optional[str]
