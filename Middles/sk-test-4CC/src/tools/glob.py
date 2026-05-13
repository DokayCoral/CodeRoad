"""Glob tool: fast file pattern matching.

Permission: read (auto-execute, no user confirmation required).
"""

from pathlib import Path

MAX_RESULTS = 1000


def glob_search(pattern: str, path_str: str = ".") -> str:
    """Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "**/*.py", "src/**/*.tsx").
        path_str: Root directory to search from.

    Returns:
        Sorted list of matching file paths (most recently modified first).
    """
    root = Path(path_str).resolve()
    if not root.exists():
        return f"[ERROR] Root path not found: {path_str}"

    try:
        matches = list(root.glob(pattern))
    except Exception as e:
        return f"[ERROR] Invalid glob pattern: {pattern} — {e}"

    if not matches:
        return f"No files matched pattern: {pattern}"

    # Filter to files only, sort by modification time (newest first)
    files = [m for m in matches if m.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Limit results
    truncated = False
    if len(files) > MAX_RESULTS:
        files = files[:MAX_RESULTS]
        truncated = True

    # Format output
    result = []
    for f in files:
        size = f.stat().st_size
        result.append(f"{f} ({_format_size(size)})")

    output = "\n".join(result)
    if truncated:
        output += f"\n\n(Results truncated at {MAX_RESULTS})"

    return output


def _format_size(size: int) -> str:
    """Format file size in human-readable form."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"
