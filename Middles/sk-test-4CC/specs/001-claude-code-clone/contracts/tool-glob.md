# Contract: Glob Tool

**Tool Name**: `glob`
**Permission Level**: `read` (auto-execute, no user confirmation)

## Description

Fast file pattern matching. Returns file paths matching a glob pattern, sorted by modification time.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| pattern | string | Yes | Glob pattern (e.g., "**/*.py", "src/**/*.tsx") |
| path | string | No | Root directory to search from (defaults to current working directory) |

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "pattern": {"type": "string", "description": "Glob pattern to match"},
    "path": {"type": "string", "description": "Root directory for search"}
  },
  "required": ["pattern"]
}
```

## Output

On success: Sorted list of matching file paths (most recently modified first).
On failure: Error message.

## Error Modes

| Error | Response |
|-------|----------|
| Invalid pattern | `[ERROR] Invalid glob pattern: <pattern>` |
| Path not found | `[ERROR] Root path not found: <path>` |
| Permission denied | `[ERROR] Permission denied: <path>` |

## Edge Cases

- No matches: Return empty list with informative message
- Symlinks: Follow and return symlink targets if they match
- Hidden files: Include dotfiles only if pattern explicitly starts with `.`
- Large directories: Limited to first 1000 matches by default
