"""Tool display with spinners and icons for CLI."""

import asyncio
import sys
from dataclasses import dataclass

TOOL_ICONS = {
    "bash": "$",
    "read_file": "->",
    "write_file": "<-",
    "edit_file": "~",
    "ls": "#",
    "glob": "*",
    "grep": "?",
}

SPINNER_FRAMES = ["...", ".. ", ".  ", ".. "]


@dataclass
class ToolDisplay:
    """State for a single tool display."""

    tool_call_id: str
    tool_name: str
    args: dict
    result: str | None = None
    spinner_idx: int = 0


class ToolDisplayManager:
    """Manages display of tool calls with spinners and icons."""

    def __init__(self):
        self.active_tools: dict[str, ToolDisplay] = {}
        self.completed_tools: list[ToolDisplay] = []
        self._pending_complete: list[ToolDisplay] = []
        self._last_line_count = 0
        self._animation_task: asyncio.Task | None = None

    def _get_icon(self, tool_name: str) -> str:
        return TOOL_ICONS.get(tool_name, ">")

    def _get_summary(self, tool: ToolDisplay) -> str:
        """Generate a short summary of the tool args."""
        args = tool.args
        if tool.tool_name == "bash" and "command" in args:
            cmd = args["command"]
            return cmd[:40] + "..." if len(cmd) > 40 else cmd
        elif tool.tool_name in ("read_file", "write_file", "edit_file") and "path" in args:
            return args["path"]
        elif tool.tool_name == "ls" and "path" in args:
            return args["path"]
        elif tool.tool_name == "glob" and "pattern" in args:
            return args["pattern"]
        elif tool.tool_name == "grep" and "pattern" in args:
            return args["pattern"]
        return ""

    def _get_result_summary(self, tool: ToolDisplay) -> str:
        """Generate a short summary of the tool result."""
        if not tool.result:
            return ""
        result = tool.result
        if tool.tool_name == "ls":
            lines = [line for line in result.strip().split("\n") if line]
            return f"{len(lines)} items"
        elif tool.tool_name in ("read_file", "glob", "grep"):
            lines = result.strip().split("\n")
            return f"{len(lines)} lines"
        elif tool.tool_name in ("write_file", "edit_file"):
            return "done"
        elif tool.tool_name == "bash":
            if len(result) > 30:
                return result[:27] + "..."
            return result.strip() or "done"
        return ""

    def start_tool(self, tool_call_id: str, tool_name: str, args: dict):
        """Register a tool as started."""
        self.active_tools[tool_call_id] = ToolDisplay(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            args=args,
        )
        self._render()
        self._start_animation()

    def end_tool(self, tool_call_id: str, result: str):
        """Mark a tool as completed."""
        if tool_call_id in self.active_tools:
            tool = self.active_tools.pop(tool_call_id)
            tool.result = result
            self.completed_tools.append(tool)
            self._pending_complete.append(tool)
            if not self.active_tools:
                self._stop_animation()
            self._render()

    def _clear_lines(self, count: int):
        """Clear the last N lines."""
        for _ in range(count):
            sys.stdout.write("\033[A")  # Move up
            sys.stdout.write("\033[2K")  # Clear line

    def _render(self):
        """Render current tool state."""
        # Only clear and redraw active tools (spinner lines)
        if self._last_line_count > 0:
            self._clear_lines(self._last_line_count)
        self._last_line_count = 0

        # Print newly completed tools permanently (won't be cleared)
        while self._pending_complete:
            tool = self._pending_complete.pop(0)
            icon = self._get_icon(tool.tool_name)
            summary = self._get_summary(tool)
            result_summary = self._get_result_summary(tool)
            line = f"  \033[32m+\033[0m {icon} {summary}"
            if result_summary:
                line += f" \033[90m-> {result_summary}\033[0m"
            print(line)

        # Print active tools (will be cleared on next render)
        for tool in self.active_tools.values():
            icon = self._get_icon(tool.tool_name)
            summary = self._get_summary(tool)
            spinner = SPINNER_FRAMES[tool.spinner_idx % len(SPINNER_FRAMES)]
            print(f"  \033[33m{spinner}\033[0m {icon} {summary}")
            self._last_line_count += 1

        sys.stdout.flush()

    def tick(self):
        """Advance spinner animation."""
        if self.active_tools:
            for tool in self.active_tools.values():
                tool.spinner_idx += 1
            self._render()

    def finalize(self):
        """Clear any remaining active tools display and reset state."""
        self._stop_animation()

        # Clear any active tool spinner lines
        if self._last_line_count > 0:
            self._clear_lines(self._last_line_count)
            self._last_line_count = 0

        # Print any remaining pending completions
        while self._pending_complete:
            tool = self._pending_complete.pop(0)
            icon = self._get_icon(tool.tool_name)
            summary = self._get_summary(tool)
            result_summary = self._get_result_summary(tool)
            line = f"  \033[32m+\033[0m {icon} {summary}"
            if result_summary:
                line += f" \033[90m-> {result_summary}\033[0m"
            print(line)

        self.completed_tools.clear()
        self.active_tools.clear()

    def _start_animation(self):
        """Start background spinner animation."""
        if self._animation_task is None or self._animation_task.done():
            self._animation_task = asyncio.create_task(self._animate())

    def _stop_animation(self):
        """Stop background spinner animation."""
        if self._animation_task and not self._animation_task.done():
            self._animation_task.cancel()
            self._animation_task = None

    async def _animate(self):
        """Background task to animate spinners."""
        try:
            while self.active_tools:
                await asyncio.sleep(0.15)
                if self.active_tools:
                    self.tick()
        except asyncio.CancelledError:
            pass
