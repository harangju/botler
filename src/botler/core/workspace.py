"""Workspace management."""

import json
from pathlib import Path

import yaml

from .schemas import AgentConfig, Message

DEFAULT_AGENT_CONFIG = """name: default
model: anthropic:claude-3-haiku-20240307
persona: |
  You are a helpful assistant with access to file system tools.
  You can read, write, and edit files in the workspace.
  Always be helpful and concise.
"""


class Workspace:
    """Manages a botler workspace directory."""

    def __init__(self, path: Path | str):
        self.path = Path(path).resolve()
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Create workspace directory structure if it doesn't exist."""
        (self.path / "agents").mkdir(parents=True, exist_ok=True)
        (self.path / "conversations").mkdir(parents=True, exist_ok=True)
        (self.path / "files").mkdir(parents=True, exist_ok=True)

    def load_agent_config(self, name: str) -> AgentConfig:
        """Load agent configuration from YAML file."""
        config_path = self.path / "agents" / name / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {config_path}")
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return AgentConfig(**data)

    def create_default_agent(self) -> AgentConfig:
        """Create the default agent if it doesn't exist."""
        agent_dir = self.path / "agents" / "default"
        config_path = agent_dir / "config.yaml"
        if not config_path.exists():
            agent_dir.mkdir(parents=True, exist_ok=True)
            config_path.write_text(DEFAULT_AGENT_CONFIG)
        return self.load_agent_config("default")

    def list_agents(self) -> list[str]:
        """List available agent names."""
        agents_dir = self.path / "agents"
        if not agents_dir.exists():
            return []
        return [
            d.name
            for d in agents_dir.iterdir()
            if d.is_dir() and (d / "config.yaml").exists()
        ]

    def _thread_path(self, thread_id: str) -> Path:
        """Get the path to a thread's message file."""
        return self.path / "conversations" / thread_id / "messages.jsonl"

    def load_messages(self, thread_id: str) -> list[Message]:
        """Load messages from a conversation thread."""
        path = self._thread_path(thread_id)
        if not path.exists():
            return []
        messages = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    messages.append(Message(**data))
        return messages

    def append_message(self, thread_id: str, message: Message) -> None:
        """Append a message to a conversation thread."""
        path = self._thread_path(thread_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(message.model_dump_json() + "\n")
