"""AgentEngine protocol and implementations."""

import json
from collections.abc import AsyncIterator
from typing import Protocol

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, UserPromptPart

from .schemas import AgentConfig, AgentContext, AgentResult, Message, ToolCall
from .tools import ALL_TOOLS, ToolDeps


class AgentEngine(Protocol):
    """Protocol for agent engines."""

    async def run(self, prompt: str, context: AgentContext, history: list[Message]) -> AgentResult:
        """Run the agent with a prompt and return the result."""
        ...

    async def run_stream(
        self, prompt: str, context: AgentContext, history: list[Message]
    ) -> AsyncIterator[str | AgentResult]:
        """Run the agent with streaming, yielding tokens then final result."""
        ...
        yield ""  # type: ignore


def _messages_to_pydantic(messages: list[Message]) -> list[ModelMessage]:
    """Convert internal messages to pydantic-ai message format."""
    result: list[ModelMessage] = []
    for msg in messages:
        if msg.role == "user":
            result.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
        # Assistant messages are handled by pydantic-ai's internal state
    return result


class PydanticEngine:
    """Agent engine using pydantic-ai."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent = Agent(
            config.model,
            system_prompt=config.persona,
            tools=ALL_TOOLS,
            deps_type=ToolDeps,
        )

    async def run(self, prompt: str, context: AgentContext, history: list[Message]) -> AgentResult:
        """Run the agent with a prompt and return the result."""
        deps = ToolDeps(workspace_path=context.workspace_path)
        message_history = _messages_to_pydantic(history) if history else None

        try:
            result = await self.agent.run(
                prompt,
                deps=deps,
                message_history=message_history,
            )

            tool_calls = []
            for msg in result.new_messages():
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        if hasattr(part, "tool_name"):
                            args = {}
                            if hasattr(part, "args") and part.args:
                                args = json.loads(part.args) if isinstance(part.args, str) else part.args
                            tool_calls.append(
                                ToolCall(name=part.tool_name, args=args, result=None)
                            )

            return AgentResult(
                response=result.output,
                tool_calls=tool_calls,
            )
        except Exception as e:
            return AgentResult(
                response="",
                error=str(e),
            )

    async def run_stream(
        self, prompt: str, context: AgentContext, history: list[Message]
    ) -> AsyncIterator[str | AgentResult]:
        """Run the agent with streaming, yielding tokens then final AgentResult."""
        deps = ToolDeps(workspace_path=context.workspace_path)
        message_history = _messages_to_pydantic(history) if history else None

        try:
            async with self.agent.run_stream(
                prompt,
                deps=deps,
                message_history=message_history,
            ) as response:
                full_response = ""
                async for token in response.stream_text(delta=True):
                    full_response += token
                    yield token

                tool_calls = []
                for msg in response.new_messages():
                    if hasattr(msg, "parts"):
                        for part in msg.parts:
                            if hasattr(part, "tool_name"):
                                args = {}
                                if hasattr(part, "args") and part.args:
                                    args = json.loads(part.args) if isinstance(part.args, str) else part.args
                                tool_calls.append(
                                    ToolCall(name=part.tool_name, args=args, result=None)
                                )

                yield AgentResult(
                    response=full_response,
                    tool_calls=tool_calls,
                )
        except Exception as e:
            yield AgentResult(
                response="",
                error=str(e),
            )
