# Contract: Bash Tool

**Tool Name**: `bash`
**Permission Level**: `shell_read` (auto for read-only) / `shell_write` (confirmation for side-effects)

## Description

Executes a shell command and returns its output. Read-only commands (ls, cat, git status, git log, git diff, etc.) auto-execute. Commands with side effects (rm, git push, npm install, pip install, etc.) require user confirmation. Dangerous commands (rm -rf /, format, mkfs, dd, >/dev/sda) are blocked and require explicit override.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| command | string | Yes | Shell command to execute |
| timeout | int | No | Timeout in seconds (default 30, max 120) |
| description | string | No | Human-readable description of what the command does (for approval UI) |

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "command": {"type": "string", "description": "Shell command to execute"},
    "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
    "description": {"type": "string", "description": "What this command does"}
  },
  "required": ["command"]
}
```

## Output

On success: stdout content + exit code.
On timeout: Partial stdout/stderr + timeout notification.
On failure: stderr content + non-zero exit code.

## Error Modes

| Error | Response |
|-------|----------|
| Command timeout | `[TIMEOUT] Command exceeded 30s limit and was terminated. Partial output: ...` |
| Command not found | `[ERROR] Command not found: <cmd>. Check spelling or PATH.` |
| Permission denied | `[ERROR] Permission denied executing: <cmd>` |
| Dangerous command detected | `[BLOCKED] Dangerous command: <cmd>. Reason: <reason>. Use --force to override.` |
| Non-zero exit | `[ERROR] Exit code <N>: <stderr>` |

## Permission Classification

**shell_read** (auto-execute): cat, ls, find, grep, git (status/log/diff/show/blame), wc, head, tail, du, df, which, echo, date, env, printenv, pwd, uname, whoami, stat, file, tree

**shell_write** (confirmation required): git (commit/push/merge/rebase/checkout/branch), npm/pip/cargo/apt/yum (install/uninstall/update), rm/mv/cp/mkdir/touch, chmod/chown, make/cmake/build, curl/wget, docker, systemctl/service, kill/pkill

**blocked** (explicit override): rm -rf /, mkfs.*, dd, fdisk, > /dev/*, :(){ :|:& };: (fork bomb)

## Edge Cases

- Non-zero exit codes: Report to user, include stderr in response so AI can suggest fixes
- Interrupt signal (Ctrl+C): Forward to subprocess, terminate cleanly
- Interactive commands: NOT supported; commands requiring stdin input are rejected (`[ERROR] Interactive commands not supported`)
- Environment inheritance: Inherits current shell environment (PATH, env vars)
