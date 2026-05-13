# Contract: Read Tool

**Tool Name**: `read`
**Permission Level**: `read` (auto-execute, no user confirmation)

## Description

Reads a file from the local filesystem at the specified path. Supports reading entire files or specific line ranges.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_path | string | Yes | Absolute path to the file to read |
| offset | int | No | Starting line number (0-indexed, for partial reads) |
| limit | int | No | Maximum number of lines to read |

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "file_path": {"type": "string", "description": "Absolute path to file"},
    "offset": {"type": "integer", "minimum": 0},
    "limit": {"type": "integer", "minimum": 1, "maximum": 2000}
  },
  "required": ["file_path"]
}
```

## Output

On success: File content as string with line number prefixes (`    1	content...`).
On failure: Error message with reason (file not found, permission denied, is a directory, etc.).

## Error Modes

| Error | Response |
|-------|----------|
| File not found | `[ERROR] File not found: <path>` |
| Permission denied | `[ERROR] Permission denied: <path>` |
| Path is directory | `[ERROR] Path is a directory, not a file: <path>` |
| File too large (>100MB) | `[ERROR] File exceeds size limit (100MB): <path>` |

## Edge Cases

- Binary files: Attempt to read → detect null bytes → warn user
- Symlinks: Follow and read target file
- offset beyond EOF: Return empty with note
