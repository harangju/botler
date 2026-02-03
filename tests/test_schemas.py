"""Tests for core schemas."""

from datetime import datetime

from botler.core.schemas import AgentConfig, AgentContext, AgentResult, Message, ToolCall


def test_tool_call():
    tc = ToolCall(name="read_file", args={"path": "test.txt"}, result="content")
    assert tc.name == "read_file"
    assert tc.args == {"path": "test.txt"}
    assert tc.result == "content"


def test_tool_call_defaults():
    tc = ToolCall(name="ls")
    assert tc.args == {}
    assert tc.result is None


def test_message():
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert isinstance(msg.timestamp, datetime)
    assert msg.agent_id is None
    assert msg.tool_calls == []


def test_message_with_tool_calls():
    tc = ToolCall(name="ls", args={"path": "."})
    msg = Message(role="assistant", content="Here are the files", tool_calls=[tc])
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].name == "ls"


def test_message_serialization():
    msg = Message(role="user", content="Test")
    json_str = msg.model_dump_json()
    restored = Message.model_validate_json(json_str)
    assert restored.role == msg.role
    assert restored.content == msg.content


def test_agent_config():
    config = AgentConfig(name="test-agent")
    assert config.name == "test-agent"
    assert config.model == "anthropic:claude-3-haiku-20240307"
    assert config.persona == "You are a helpful assistant."


def test_agent_config_custom():
    config = AgentConfig(
        name="custom",
        model="anthropic:claude-haiku-3",
        persona="Be brief.",
    )
    assert config.model == "anthropic:claude-haiku-3"
    assert config.persona == "Be brief."


def test_agent_context(tmp_path):
    ctx = AgentContext(thread_id="t1", workspace_path=tmp_path)
    assert ctx.thread_id == "t1"
    assert ctx.user_id is None
    assert ctx.workspace_path == tmp_path
    assert ctx.referenced_files == []


def test_agent_result():
    result = AgentResult(response="Done")
    assert result.response == "Done"
    assert result.files_modified == []
    assert result.tool_calls == []
    assert result.error is None


def test_agent_result_with_error():
    result = AgentResult(response="", error="API failed")
    assert result.error == "API failed"
