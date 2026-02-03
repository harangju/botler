"""Tests for file tools."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from botler.core.tools import (
    ToolDeps,
    bash,
    edit_file,
    glob,
    grep,
    ls,
    read_file,
    write_file,
)


@dataclass
class MockContext:
    """Mock RunContext for testing."""

    deps: ToolDeps


@pytest.fixture
def ctx(tmp_path):
    """Create a mock context with a temporary workspace."""
    return MockContext(deps=ToolDeps(workspace_path=tmp_path))


class TestReadFile:
    def test_read_existing_file(self, ctx):
        (ctx.deps.workspace_path / "test.txt").write_text("Hello World")
        result = read_file(ctx, "test.txt")
        assert result == "Hello World"

    def test_read_nonexistent_file(self, ctx):
        result = read_file(ctx, "missing.txt")
        assert "Error: File not found" in result

    def test_read_directory(self, ctx):
        (ctx.deps.workspace_path / "subdir").mkdir()
        result = read_file(ctx, "subdir")
        assert "Error: Not a file" in result

    def test_read_nested_file(self, ctx):
        subdir = ctx.deps.workspace_path / "a" / "b"
        subdir.mkdir(parents=True)
        (subdir / "nested.txt").write_text("Nested content")
        result = read_file(ctx, "a/b/nested.txt")
        assert result == "Nested content"


class TestWriteFile:
    def test_write_new_file(self, ctx):
        result = write_file(ctx, "new.txt", "Content")
        assert "Successfully wrote" in result
        assert (ctx.deps.workspace_path / "new.txt").read_text() == "Content"

    def test_write_creates_directories(self, ctx):
        result = write_file(ctx, "a/b/c/deep.txt", "Deep")
        assert "Successfully wrote" in result
        assert (ctx.deps.workspace_path / "a/b/c/deep.txt").read_text() == "Deep"

    def test_write_overwrites_existing(self, ctx):
        (ctx.deps.workspace_path / "existing.txt").write_text("Old")
        write_file(ctx, "existing.txt", "New")
        assert (ctx.deps.workspace_path / "existing.txt").read_text() == "New"


class TestEditFile:
    def test_edit_replaces_string(self, ctx):
        (ctx.deps.workspace_path / "edit.txt").write_text("Hello World")
        result = edit_file(ctx, "edit.txt", "World", "Universe")
        assert "Replaced 1 occurrence" in result
        assert (ctx.deps.workspace_path / "edit.txt").read_text() == "Hello Universe"

    def test_edit_multiple_occurrences(self, ctx):
        (ctx.deps.workspace_path / "multi.txt").write_text("foo bar foo baz foo")
        result = edit_file(ctx, "multi.txt", "foo", "qux")
        assert "Replaced 3 occurrence" in result

    def test_edit_string_not_found(self, ctx):
        (ctx.deps.workspace_path / "nope.txt").write_text("Hello")
        result = edit_file(ctx, "nope.txt", "Goodbye", "Hi")
        assert "Error: String not found" in result

    def test_edit_nonexistent_file(self, ctx):
        result = edit_file(ctx, "missing.txt", "a", "b")
        assert "Error: File not found" in result


class TestLs:
    def test_ls_empty_directory(self, ctx):
        result = ls(ctx, ".")
        assert result == "(empty directory)"

    def test_ls_with_files(self, ctx):
        (ctx.deps.workspace_path / "a.txt").touch()
        (ctx.deps.workspace_path / "b.txt").touch()
        result = ls(ctx, ".")
        assert "a.txt" in result
        assert "b.txt" in result

    def test_ls_shows_directories_with_slash(self, ctx):
        (ctx.deps.workspace_path / "subdir").mkdir()
        result = ls(ctx, ".")
        assert "subdir/" in result

    def test_ls_nonexistent(self, ctx):
        result = ls(ctx, "missing")
        assert "Error: Directory not found" in result

    def test_ls_file_not_directory(self, ctx):
        (ctx.deps.workspace_path / "file.txt").touch()
        result = ls(ctx, "file.txt")
        assert "Error: Not a directory" in result


class TestGlob:
    def test_glob_matches_files(self, ctx):
        (ctx.deps.workspace_path / "a.py").touch()
        (ctx.deps.workspace_path / "b.py").touch()
        (ctx.deps.workspace_path / "c.txt").touch()
        result = glob(ctx, "*.py")
        assert "a.py" in result
        assert "b.py" in result
        assert "c.txt" not in result

    def test_glob_recursive(self, ctx):
        subdir = ctx.deps.workspace_path / "sub"
        subdir.mkdir()
        (ctx.deps.workspace_path / "root.py").touch()
        (subdir / "nested.py").touch()
        result = glob(ctx, "**/*.py")
        assert "root.py" in result
        assert "sub/nested.py" in result

    def test_glob_no_matches(self, ctx):
        result = glob(ctx, "*.xyz")
        assert "No files matching" in result


class TestGrep:
    def test_grep_finds_pattern(self, ctx):
        (ctx.deps.workspace_path / "search.txt").write_text("line one\nline two\nline three")
        result = grep(ctx, "two", "search.txt")
        assert "search.txt:2:" in result
        assert "line two" in result

    def test_grep_regex(self, ctx):
        (ctx.deps.workspace_path / "regex.txt").write_text("foo123bar\nfoo456bar")
        result = grep(ctx, r"foo\d+bar", "regex.txt")
        assert "regex.txt:1:" in result
        assert "regex.txt:2:" in result

    def test_grep_no_matches(self, ctx):
        (ctx.deps.workspace_path / "empty.txt").write_text("nothing here")
        result = grep(ctx, "missing", "empty.txt")
        assert "No matches" in result

    def test_grep_invalid_regex(self, ctx):
        result = grep(ctx, "[invalid", ".")
        assert "Error: Invalid regex" in result

    def test_grep_directory(self, ctx):
        (ctx.deps.workspace_path / "a.txt").write_text("findme")
        (ctx.deps.workspace_path / "b.txt").write_text("other")
        result = grep(ctx, "findme", ".")
        assert "a.txt" in result
        assert "b.txt" not in result


class TestBash:
    def test_bash_simple_command(self, ctx):
        result = bash(ctx, "echo hello")
        assert "hello" in result

    def test_bash_runs_in_workspace(self, ctx):
        (ctx.deps.workspace_path / "marker.txt").touch()
        result = bash(ctx, "ls")
        assert "marker.txt" in result

    def test_bash_captures_stderr(self, ctx):
        result = bash(ctx, "ls nonexistent_file_xyz 2>&1 || true")
        # Just verify it doesn't crash
        assert isinstance(result, str)

    def test_bash_returns_exit_code_on_failure(self, ctx):
        result = bash(ctx, "exit 42")
        assert "Return code: 42" in result


class TestPathSecurity:
    def test_cannot_escape_workspace(self, ctx):
        with pytest.raises(ValueError, match="escapes workspace"):
            read_file(ctx, "../../../etc/passwd")

    def test_cannot_escape_with_absolute_path(self, ctx):
        with pytest.raises(ValueError, match="escapes workspace"):
            read_file(ctx, "/etc/passwd")
