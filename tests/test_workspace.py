"""Tests for workspace management."""

import json

import pytest

from botler.core.schemas import Message
from botler.core.workspace import Workspace


def test_workspace_creates_structure(tmp_path):
    ws = Workspace(tmp_path / "myworkspace")
    assert (ws.path / "agents").is_dir()
    assert (ws.path / "conversations").is_dir()
    assert (ws.path / "files").is_dir()


def test_workspace_existing_dir(tmp_path):
    (tmp_path / "existing").mkdir()
    ws = Workspace(tmp_path / "existing")
    assert ws.path.exists()


def test_list_agents_empty(tmp_path):
    ws = Workspace(tmp_path)
    assert ws.list_agents() == []


def test_create_default_agent(tmp_path):
    ws = Workspace(tmp_path)
    config = ws.create_default_agent()
    assert config.name == "default"
    assert "default" in ws.list_agents()
    assert (ws.path / "agents" / "default" / "config.yaml").exists()


def test_create_default_agent_idempotent(tmp_path):
    ws = Workspace(tmp_path)
    config1 = ws.create_default_agent()
    config2 = ws.create_default_agent()
    assert config1.name == config2.name


def test_load_agent_config(tmp_path):
    ws = Workspace(tmp_path)
    ws.create_default_agent()
    config = ws.load_agent_config("default")
    assert config.name == "default"
    assert "anthropic:" in config.model


def test_load_agent_config_not_found(tmp_path):
    ws = Workspace(tmp_path)
    with pytest.raises(FileNotFoundError):
        ws.load_agent_config("nonexistent")


def test_list_agents(tmp_path):
    ws = Workspace(tmp_path)
    assert ws.list_agents() == []
    ws.create_default_agent()
    assert ws.list_agents() == ["default"]


def test_append_and_load_messages(tmp_path):
    ws = Workspace(tmp_path)
    thread_id = "test-thread"

    msg1 = Message(role="user", content="Hello")
    msg2 = Message(role="assistant", content="Hi there")

    ws.append_message(thread_id, msg1)
    ws.append_message(thread_id, msg2)

    messages = ws.load_messages(thread_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "Hello"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Hi there"


def test_load_messages_empty_thread(tmp_path):
    ws = Workspace(tmp_path)
    messages = ws.load_messages("nonexistent")
    assert messages == []


def test_messages_persist_to_jsonl(tmp_path):
    ws = Workspace(tmp_path)
    thread_id = "persist-test"

    msg = Message(role="user", content="Test message")
    ws.append_message(thread_id, msg)

    jsonl_path = ws.path / "conversations" / thread_id / "messages.jsonl"
    assert jsonl_path.exists()

    with open(jsonl_path) as f:
        line = f.readline()
        data = json.loads(line)
        assert data["role"] == "user"
        assert data["content"] == "Test message"


def test_thread_creates_directory(tmp_path):
    ws = Workspace(tmp_path)
    thread_id = "new-thread"
    msg = Message(role="user", content="First message")
    ws.append_message(thread_id, msg)

    thread_dir = ws.path / "conversations" / thread_id
    assert thread_dir.is_dir()
