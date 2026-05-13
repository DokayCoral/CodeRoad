# Contract: Grep Tool

**Tool Name**: `grep`
**Permission Level**: `read` (auto-execute, no user confirmation)

## Description

Searches file contents using regular expression pattern matching. Supports file type filtering and context lines.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| pattern | string | Yes | Regular expression to search for |
| path | string | No | File or directory to search in (defaults to current working directory) |
| glob | string | No | File pattern filter (e.g., "*.py", "*.{ts,tsx}") |
| output_mode | string | No | "content" (default), "files_with_matches", or "count" |
| context | int | No | Number of surrounding lines to show (maps to -C) |
| -i | bool | No | Case-insensitive search |
| head_limit | int | No | Max results to return (default 250) |
| multiline | bool | No | Enable multiline mode (. matches newlines) |

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "pattern": {"type": "string", "description": "Regex pattern to search for"},
    "path": {"type": "string", "description": "File or directory path"},
    "glob": {"type": "string", "description": "File pattern filter"},
    "output_mode": {"type": "string", "enum": ["content", "files_with_matches", "count"]},
    "context": {"type": "integer", "minimum": 0, "maximum": 10},
    "-i": {"type": "boolean"},
    "head_limit": {"type": "integer", "minimum": 1, "maximum": 500},
    "multiline": {"type": "boolean"}
  },
  "required": ["pattern"]
}
```

## Output

On success (content mode): Matching lines with file path, line number, and content.
On success (files_with_matches): List of matching file paths.
On success (count): File path and match count pairs.

## Error Modes

| Error | Response |
|-------|----------|
| Invalid regex | `[ERROR] Invalid regular expression: <pattern>. <specific_error>` |
| Path not found | `[ERROR] Path not found: <path>` |
| Permission denied | `[ERROR] Permission denied reading: <path>` |

## Edge Cases

- Binary files: Automatically skipped (check first 8KB for null bytes)
- `.gitignore` patterns: Respected by default (skip .git/ and common binary dirs)
- Very large result sets: Truncated at head_limit (default 250)
