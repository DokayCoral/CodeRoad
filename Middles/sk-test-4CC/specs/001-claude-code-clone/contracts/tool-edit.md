# Contract: Edit Tool

**Tool Name**: `edit`
**Permission Level**: `write` (requires user confirmation)

## Description

Performs exact string replacement in an existing file. Searches for `old_string` and replaces it with `new_string`. Fails if `old_string` is not unique in the file.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_path | string | Yes | Absolute path to the file to edit |
| old_string | string | Yes | Exact text to find and replace |
| new_string | string | Yes | Replacement text |

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "file_path": {"type": "string", "description": "Absolute path to file"},
    "old_string": {"type": "string", "description": "Exact text to replace"},
    "new_string": {"type": "string", "description": "Replacement text"}
  },
  "required": ["file_path", "old_string", "new_string"]
}
```

## Output

On success: Confirmation with line range affected.
On failure: Error message with specific reason.

## Error Modes

| Error | Response |
|-------|----------|
| File not found | `[ERROR] File not found: <path>`. Suggest using Write tool to create. |
| old_string not found | `[ERROR] Text not found in file: <path>` |
| old_string not unique | `[ERROR] Text found N times; must be unique. Provide more context.` |
| old_string == new_string | `[ERROR] old_string and new_string are identical` |

## Edge Cases

- File changed externally since last read → Detect modification timestamp change; warn user with conflict resolution (overwrite/skip/diff)
- Whitespace sensitivity → Match is exact (including tabs/spaces); strip trailing whitespace from both strings silently to reduce friction
- Large files (>10k lines) → Still supported; exact string match may be slower but correct
