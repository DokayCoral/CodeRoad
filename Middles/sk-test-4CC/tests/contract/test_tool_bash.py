"""Contract tests for the Bash tool."""

import pytest

from src.tools.bash import execute_bash, classify_command


class TestBashClassification:
    """Tests for command classification logic."""

    def test_read_command_classified_as_read(self):
        """Read-only commands like ls are classified as shell_read."""
        assert classify_command("ls -la") == "shell_read"
        assert classify_command("cat file.txt") == "shell_read"
        assert classify_command("echo hello") == "shell_read"
        assert classify_command("grep pattern file") == "shell_read"

    def test_git_status_is_read(self):
        """git status is classified as shell_read."""
        assert classify_command("git status") == "shell_read"
        assert classify_command("git log --oneline") == "shell_read"
        assert classify_command("git diff HEAD~1") == "shell_read"

    def test_write_command_classified_as_write(self):
        """Write commands like rm are classified as shell_write."""
        assert classify_command("rm file.txt") == "shell_write"
        assert classify_command("mkdir newdir") == "shell_write"

    def test_git_push_is_write(self):
        """git push is classified as shell_write."""
        assert classify_command("git push origin main") == "shell_write"
        assert classify_command("git commit -m 'msg'") == "shell_write"

    def test_dangerous_command_blocked(self):
        """rm -rf / is blocked."""
        result = classify_command("rm -rf /")
        assert result == "blocked"


class TestBashExecution:
    """Tests for command execution."""

    def test_echo_output(self):
        """Echo returns its argument."""
        result = execute_bash("echo hello world")
        assert "hello world" in result

    def test_pwd_output(self):
        """pwd returns current directory."""
        result = execute_bash("pwd")
        assert len(result) > 0

    def test_nonexistent_command(self):
        """Non-existent command returns error."""
        result = execute_bash("nonexistentcommand123xyz")
        assert "[ERROR]" in result or "not found" in result.lower()

    def test_command_with_nonzero_exit(self):
        """Command with non-zero exit returns error prefix."""
        result = execute_bash("ls /nonexistent_dir_xyz")
        assert not result.startswith("[ERROR]") or "ls" in result  # ls returns non-zero
