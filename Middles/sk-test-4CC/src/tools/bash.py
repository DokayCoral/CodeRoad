"""Bash tool: shell command execution with safety gates.

Permission: shell_read (auto for read-only commands) / shell_write (confirmation).
Blocked dangerous commands require explicit override.

Classification:
- shell_read: cat, ls, git status/log/diff, find, grep, echo, pwd, etc.
- shell_write: git commit/push, npm/pip install, rm, mv, mkdir, etc.
- blocked: rm -rf /, mkfs.*, dd, fork bombs
"""

import os
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120

# Commands classified as read-only (safe auto-execute)
SHELL_READ_COMMANDS = {
    "cat", "less", "head", "tail", "more", "zcat", "bzcat",
    "ls", "dir", "vdir", "tree",
    "find", "locate", "which", "whereis", "type",
    "grep", "egrep", "fgrep", "rg", "ag",
    "git",  # Only specific subcommands considered read-only
    "wc", "sort", "uniq", "cut", "tr", "column",
    "du", "df", "stat", "file",
    "echo", "printf", "date", "cal",
    "env", "printenv", "pwd", "whoami", "id", "uname", "hostname",
    "ps", "top", "htop", "uptime", "free",
    "diff", "cmp", "comm", "md5sum", "sha1sum", "sha256sum",
}

# Read-only git subcommands
GIT_READ_SUBCOMMANDS = {
    "status", "log", "diff", "show", "blame", "branch",
    "tag", "remote", "config", "ls-files", "rev-parse",
    "rev-list", "describe", "stash", "shortlog",
}

# Commands with side effects (need confirmation)
SHELL_WRITE_COMMANDS = {
    "rm", "mv", "cp", "mkdir", "rmdir", "touch", "chmod", "chown",
    "git",  # Write subcommands classified separately
    "npm", "npx", "yarn", "pnpm", "pip", "pip3", "python", "python3",
    "cargo", "go", "rustc", "gcc", "g++", "make", "cmake", "ninja",
    "curl", "wget",
    "docker", "docker-compose", "kubectl",
    "systemctl", "service",
    "kill", "pkill", "killall",
    "ssh", "scp", "rsync",
    "tar", "zip", "unzip", "gzip", "gunzip",
    "sed", "awk",  # When used with -i (in-place) flag
    "tee",
    "mount", "umount",
}

# Pattern-based dangerous command detection
BLOCKED_PATTERNS = [
    (["rm", "-rf", "/"], "rm -rf / is destructive to the entire filesystem"),
    (["rm", "-rf", "/*"], "rm -rf /* is destructive to the entire filesystem"),
    (["mkfs"], "mkfs formats filesystems destructively"),
    (["dd", "if="], "dd can overwrite disks; verify target carefully"),
    (["fdisk"], "fdisk modifies disk partitions destructively"),
    (["format"], "format command may format disks"),
    (["shutdown"], "shutdown affects the entire system"),
    (["reboot"], "reboot affects the entire system"),
    ([":(){ :|:& };:"], "Fork bomb detected"),
    (["fork", "bomb"], "Potential fork bomb detected"),
]


def classify_command(command: str) -> str:
    """Classify a shell command as shell_read, shell_write, or blocked.

    Returns one of: "shell_read", "shell_write", "blocked"
    """
    if not command.strip():
        return "shell_read"

    # Parse the command
    try:
        parts = shlex.split(command)
    except ValueError:
        return "shell_write"  # Malformed command, require approval

    if not parts:
        return "shell_read"

    # Check for pipe chains: any write in the chain makes it write
    commands_in_chain = []
    current_cmd = []
    for part in parts:
        if part in ("|", "|&", "&&", ";", "||"):
            if current_cmd:
                commands_in_chain.append(current_cmd)
                current_cmd = []
        else:
            current_cmd.append(part)
    if current_cmd:
        commands_in_chain.append(current_cmd)

    has_write = False
    for cmd_parts in commands_in_chain:
        classification = _classify_single_command(cmd_parts)
        if classification == "blocked":
            return "blocked"
        if classification == "shell_write":
            has_write = True

    return "shell_write" if has_write else "shell_read"


def _classify_single_command(parts: list[str]) -> str:
    """Classify a single command (no pipes/chains)."""
    if not parts:
        return "shell_read"

    base = os.path.basename(parts[0])

    # Check blocked patterns
    for pattern, reason in BLOCKED_PATTERNS:
        cmd_str = " ".join(parts)
        if all(p in cmd_str for p in pattern):
            return "blocked"

    # Check interactive commands
    if base in ("vim", "vi", "nano", "emacs", "less", "more", "top", "htop",
                 "ssh", "telnet", "screen", "tmux", "su", "sudo", "passwd",
                 "mysql", "psql", "sqlite3"):
        return "shell_write"  # Interactive, require approval

    # Git subcommand classification
    if base == "git" and len(parts) > 1:
        subcmd = parts[1]
        if subcmd in GIT_READ_SUBCOMMANDS:
            return "shell_read"
        return "shell_write"

    # Check for -i flag in sed (in-place edit)
    if base in ("sed", "awk") and "-i" in parts:
        return "shell_write"

    # Check for redirects (> or >>)
    if any(op in parts for op in (">", ">>", "2>", "&>")):
        return "shell_write"

    if base in SHELL_READ_COMMANDS:
        return "shell_read"

    if base in SHELL_WRITE_COMMANDS:
        return "shell_write"

    # Unknown commands default to shell_write (conservative)
    return "shell_write"


def execute_bash(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    description: str = "",
) -> str:
    """Execute a shell command and return its output.

    Args:
        command: Shell command string to execute.
        timeout: Timeout in seconds (1-120).
        description: Human-readable description for approval UI.

    Returns:
        stdout output, or error message prefixed with [ERROR]/[TIMEOUT]/[BLOCKED].
    """
    if not command.strip():
        return "[ERROR] Empty command"

    # Clamp timeout
    timeout = max(1, min(timeout, MAX_TIMEOUT))

    # Check classification
    classification = classify_command(command)
    if classification == "blocked":
        return (
            f"[BLOCKED] Dangerous command detected. "
            f"Use --force to override if you are absolutely sure: {command}"
        )

    # Reject interactive commands
    base = os.path.basename(shlex.split(command)[0]) if command.strip() else ""
    if base in ("ssh", "vim", "vi", "nano", "emacs", "screen", "tmux",
                "mysql", "psql", "sqlite3", "less", "more"):
        return f"[ERROR] Interactive commands not supported: {base}"

    try:
        # Use subprocess.run with shell=False for safety (parse the command ourselves)
        # But for practical reasons with complex commands, we use shell=True with timeout
        # The safety comes from the classification layer above
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
            env=os.environ.copy(),
        )

        output = result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr

        if result.returncode != 0:
            if not output:
                output = f"(exit code {result.returncode})"
            return f"[ERROR] Exit code {result.returncode}:\n{output.strip()}"

        return output.strip() or f"(exit code 0: no output)"

    except subprocess.TimeoutExpired:
        return (
            f"[TIMEOUT] Command exceeded {timeout}s limit and was terminated.\n"
            f"Command: {command}"
        )
    except FileNotFoundError:
        return f"[ERROR] Command not found: {command}. Check spelling or PATH."
    except PermissionError as e:
        return f"[ERROR] Permission denied executing: {command} — {e}"
    except Exception as e:
        return f"[ERROR] Command execution failed: {e}"
