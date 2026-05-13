# Contract: Write Tool

**Tool Name**: `write`
**Permission Level**: `write` (requires user confirmation)

## Description

Creates a new file or overwrites an existing file at the specified path. If the target file does not exist, prompts user to confirm creation (including parent directories).

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_path | string | Yes | Absolute path to write to |
| content | string | Yes | Content to write to the file |

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "file_path": {"type": "string", "description": "Absolute path to file"},
    "content": {"type": "string", "description": "Full file content to write"}
  },
  "required": ["file_path", "content"]
}
```

## Output

On success: Confirmation message with file path and size.
On failure: Error message with reason.

## Error Modes

| Error | Response |
|-------|----------|
| Permission denied | `[ERROR] Permission denied: <path>` |
| Path is directory | `[ERROR] Cannot overwrite directory: <path>` |
| Parent directory not writable | `[ERROR] Cannot create parent directories: <parent_path>` |
| Disk full | `[ERROR] Disk full or quota exceeded` |

## Edge Cases

- File does not exist → Prompt user: "Create new file `<path>`?" before writing
- Parent directories missing → Auto-create parent directories after user confirms file creation
- Overwriting existing file → Auto-backup original as `<filename>.bak` before writing
- External modification conflict → Detect if file changed since last read; warn user
