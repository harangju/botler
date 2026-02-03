"""File tools (read, write, edit, etc.)."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import RunContext


@dataclass
class ToolDeps:
    """Dependencies injected into tools."""

    workspace_path: Path


def _resolve_path(ctx: RunContext[ToolDeps], path: str) -> Path:
    """Resolve a path relative to the workspace, ensuring it stays within bounds."""
    workspace = ctx.deps.workspace_path.resolve()
    resolved = (workspace / path).resolve()
    if not str(resolved).startswith(str(workspace)):
        raise ValueError(f"Path {path} escapes workspace boundary")
    return resolved


def read_file(ctx: RunContext[ToolDeps], path: str) -> str:
    """Read the contents of a file."""
    resolved = _resolve_path(ctx, path)
    if not resolved.exists():
        return f"Error: File not found: {path}"
    if not resolved.is_file():
        return f"Error: Not a file: {path}"
    return resolved.read_text()


def write_file(ctx: RunContext[ToolDeps], path: str, content: str) -> str:
    """Write content to a file, creating directories if needed."""
    resolved = _resolve_path(ctx, path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content)
    return f"Successfully wrote {len(content)} bytes to {path}"


def edit_file(ctx: RunContext[ToolDeps], path: str, old: str, new: str) -> str:
    """Replace a string in a file."""
    resolved = _resolve_path(ctx, path)
    if not resolved.exists():
        return f"Error: File not found: {path}"
    content = resolved.read_text()
    if old not in content:
        return f"Error: String not found in {path}"
    count = content.count(old)
    new_content = content.replace(old, new)
    resolved.write_text(new_content)
    return f"Replaced {count} occurrence(s) in {path}"


def ls(ctx: RunContext[ToolDeps], path: str = ".") -> str:
    """List contents of a directory."""
    resolved = _resolve_path(ctx, path)
    if not resolved.exists():
        return f"Error: Directory not found: {path}"
    if not resolved.is_dir():
        return f"Error: Not a directory: {path}"
    entries = []
    for entry in sorted(resolved.iterdir()):
        suffix = "/" if entry.is_dir() else ""
        entries.append(entry.name + suffix)
    if not entries:
        return "(empty directory)"
    return "\n".join(entries)


def glob(ctx: RunContext[ToolDeps], pattern: str) -> str:
    """Find files matching a glob pattern."""
    workspace = ctx.deps.workspace_path
    matches = list(workspace.glob(pattern))
    if not matches:
        return f"No files matching: {pattern}"
    relative = [str(m.relative_to(workspace)) for m in matches if m.is_file()]
    return "\n".join(sorted(relative))


def grep(ctx: RunContext[ToolDeps], pattern: str, path: str = ".") -> str:
    """Search for a pattern in files."""
    resolved = _resolve_path(ctx, path)
    workspace = ctx.deps.workspace_path
    results = []

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    if resolved.is_file():
        files = [resolved]
    elif resolved.is_dir():
        files = [f for f in resolved.rglob("*") if f.is_file()]
    else:
        return f"Error: Path not found: {path}"

    for file in files:
        try:
            content = file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if regex.search(line):
                    rel_path = file.relative_to(workspace)
                    results.append(f"{rel_path}:{i}: {line}")
        except (UnicodeDecodeError, PermissionError):
            continue

    if not results:
        return f"No matches for pattern: {pattern}"
    return "\n".join(results[:100])  # Limit output


def bash(ctx: RunContext[ToolDeps], command: str) -> str:
    """Execute a shell command in the workspace directory."""
    workspace = ctx.deps.workspace_path
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        if result.returncode != 0:
            output += f"\nReturn code: {result.returncode}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {e}"


ALL_TOOLS = [read_file, write_file, edit_file, ls, glob, grep, bash]
