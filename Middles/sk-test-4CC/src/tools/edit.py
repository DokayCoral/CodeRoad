"""Edit tool: exact string replacement in files.

Permission: write (requires user confirmation).
"""

import os
from pathlib import Path


def edit_file(file_path: str, old_string: str, new_string: str) -> str:
    """Replace old_string with new_string in a file using exact match.

    Args:
        file_path: Absolute path to the file.
        old_string: Exact text to find and replace (must be unique).
        new_string: Replacement text.

    Returns:
        Success message or error.
    """
    path = Path(file_path).resolve()

    if not path.exists():
        return f"[ERROR] File not found: {file_path}. Use the Write tool to create a new file."
    if not path.is_file():
        return f"[ERROR] Path is a directory: {file_path}"

    # Read file
    try:
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
    except OSError as e:
        return f"[ERROR] Cannot read file: {file_path} — {e}"

    # Normalize trailing whitespace for robust matching (strip trailing whitespace on each line of old_string)
    old_normalized = "\n".join(line.rstrip() for line in old_string.split("\n"))

    # Check old_string == new_string
    if old_string == new_string:
        return "[ERROR] old_string and new_string are identical"

    # Count occurrences
    count = original.count(old_string)
    if count == 0:
        return f"[ERROR] Text not found in file: {file_path}"
    if count > 1:
        return f"[ERROR] Text found {count} times; must be unique. Provide more surrounding context."

    # Check for external modification
    try:
        mtime_before = os.path.getmtime(path)
    except OSError:
        mtime_before = None

    # Perform replacement
    modified = original.replace(old_string, new_string, 1)

    # Detect which lines were affected
    original_lines = original.split("\n")
    modified_lines = modified.split("\n")
    changed_start = None
    changed_end = None
    max_lines = min(len(original_lines), len(modified_lines))
    for i in range(max_lines):
        o = original_lines[i]
        m = modified_lines[i]
        if o != m:
            if changed_start is None:
                changed_start = i + 1
            changed_end = i + 1

    # Check external modification again (could have changed during our work)
    try:
        if mtime_before is not None and os.path.getmtime(path) != mtime_before:
            return (
                "[ERROR] File was modified externally since last read. "
                "Re-read the file and try the edit again."
            )
    except OSError:
        pass

    # Write
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(modified)
    except OSError as e:
        return f"[ERROR] Cannot write file: {file_path} — {e}"

    if changed_start:
        return f"Edited {file_path}: lines {changed_start}-{changed_end} modified"
    else:
        return f"Edited {file_path}"
