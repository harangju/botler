"""CLI entrypoint for Botler."""

import asyncio
import sys
import uuid
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

from botler import __version__
from botler.cli.display import ToolDisplayManager
from botler.core.engine import PydanticEngine
from botler.core.schemas import AgentContext, AgentResult, Message, ToolEndEvent, ToolStartEvent
from botler.core.workspace import Workspace


@click.group()
@click.version_option(version=__version__, prog_name="botler")
def main():
    """Botler - An agent runtime you own."""
    pass


@main.command()
@click.option(
    "--workspace",
    "-w",
    type=click.Path(path_type=Path),
    default=Path("workspace"),
    help="Path to workspace directory",
)
@click.option(
    "--agent",
    "-a",
    default="default",
    help="Agent name to use",
)
@click.option(
    "--thread",
    "-t",
    default=None,
    help="Thread ID (auto-generated if not provided)",
)
def chat(workspace: Path, agent: str, thread: str | None):
    """Start a chat session with an agent."""
    asyncio.run(_chat_async(workspace, agent, thread))


async def _chat_async(workspace_path: Path, agent_name: str, thread_id: str | None):
    """Async implementation of chat command."""
    ws = Workspace(workspace_path)

    if agent_name == "default" and "default" not in ws.list_agents():
        click.echo(f"Creating default agent in {workspace_path}/agents/default/")
        ws.create_default_agent()

    try:
        config = ws.load_agent_config(agent_name)
    except FileNotFoundError:
        click.echo(f"Agent '{agent_name}' not found. Available agents: {ws.list_agents()}")
        return

    thread_id = thread_id or str(uuid.uuid4())[:8]
    click.echo(f"Chat session started (agent: {agent_name}, thread: {thread_id})")
    click.echo("Type 'exit' or Ctrl+C to quit.\n")

    engine = PydanticEngine(config)
    context = AgentContext(
        thread_id=thread_id,
        workspace_path=ws.path,
    )

    while True:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (KeyboardInterrupt, EOFError):
            click.echo("\nGoodbye!")
            break

        if user_input.lower() in ("exit", "quit"):
            click.echo("Goodbye!")
            break

        user_msg = Message(role="user", content=user_input)
        ws.append_message(thread_id, user_msg)

        history = ws.load_messages(thread_id)

        click.echo("Agent> ", nl=False)
        result = None
        display = ToolDisplayManager()
        text_started = False

        async for chunk in engine.run_stream_with_events(user_input, context, history[:-1]):
            if isinstance(chunk, ToolStartEvent):
                if text_started:
                    click.echo()
                    text_started = False
                display.start_tool(chunk.tool_call_id, chunk.tool_name, chunk.args)
            elif isinstance(chunk, ToolEndEvent):
                display.end_tool(chunk.tool_call_id, chunk.result)
            elif isinstance(chunk, AgentResult):
                result = chunk
            else:
                if not text_started and display.completed_tools:
                    display.finalize()
                    click.echo("Agent> ", nl=False)
                text_started = True
                click.echo(chunk, nl=False)
                sys.stdout.flush()

        if display.active_tools or display.completed_tools:
            display.finalize()

        click.echo()

        if result and result.error:
            click.echo(f"Error: {result.error}")

        assistant_msg = Message(
            role="assistant",
            content=result.response if result else "",
            agent_id=agent_name,
            tool_calls=result.tool_calls if result else [],
        )
        ws.append_message(thread_id, assistant_msg)
        click.echo()


if __name__ == "__main__":
    main()
