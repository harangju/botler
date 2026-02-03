"""CLI entrypoint for Botler."""

import asyncio
import uuid
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

from botler import __version__
from botler.core.engine import PydanticEngine
from botler.core.schemas import AgentContext, Message
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
        result = await engine.run(user_input, context, history[:-1])

        if result.error:
            click.echo(f"Error: {result.error}")
        else:
            click.echo(result.response)

        if result.tool_calls:
            tools_used = ", ".join(tc.name for tc in result.tool_calls)
            click.echo(click.style(f"  [tools: {tools_used}]", fg="cyan"))

        assistant_msg = Message(
            role="assistant",
            content=result.response,
            agent_id=agent_name,
            tool_calls=result.tool_calls,
        )
        ws.append_message(thread_id, assistant_msg)
        click.echo()


if __name__ == "__main__":
    main()
