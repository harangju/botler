"""CLI entrypoint for Botler."""

import click

from botler import __version__


@click.group()
@click.version_option(version=__version__, prog_name="botler")
def main():
    """Botler - An agent runtime you own."""
    pass


@main.command()
def chat():
    """Start a chat session with an agent."""
    click.echo("Chat not implemented yet.")


if __name__ == "__main__":
    main()
