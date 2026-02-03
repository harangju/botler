"""Message, AgentConfig, and other data schemas."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A tool call made by an agent."""

    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None


class Message(BaseModel):
    """A message in a conversation."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)


class AgentConfig(BaseModel):
    """Configuration for an agent, loaded from YAML."""

    name: str
    model: str = "anthropic:claude-3-5-haiku-20241022"
    persona: str = "You are a helpful assistant."


class AgentContext(BaseModel):
    """Context passed to an agent during execution."""

    thread_id: str
    user_id: str | None = None
    workspace_path: Path
    referenced_files: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Result from an agent run."""

    response: str
    files_modified: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    error: str | None = None


@dataclass
class ToolStartEvent:
    """Emitted when a tool call starts."""

    tool_call_id: str
    tool_name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolEndEvent:
    """Emitted when a tool call completes."""

    tool_call_id: str
    result: str
