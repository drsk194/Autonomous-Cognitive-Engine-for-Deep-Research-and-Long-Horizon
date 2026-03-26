"""
state.py
State management for the Autonomous Cognitive Engine.
Supports Milestone 1 (planning), Milestone 2 (file system), Milestone 3 (sub-agent delegation).
"""

from typing import TypedDict, List, Dict, Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class Todo(TypedDict):
    task: str
    status: str       # "pending" | "completed"
    result: Optional[str]


class AgentState(TypedDict):
    """
    Shared state for the full Deep Research agent.

    Fields:
        messages         : Full conversation + tool call history (reduced via add_messages).
        todos            : Structured TODO list created by write_todos.
        current_task_index : Index of the TODO currently being executed (None = done).
        files            : Virtual file system  {filename -> content}.
        execution_log    : Human-readable trace of every major step.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    todos: List[Todo]
    current_task_index: Optional[int]
    files: Dict[str, str]
    execution_log: List[str]
    



