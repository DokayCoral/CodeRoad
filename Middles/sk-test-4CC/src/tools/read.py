"""Read tool: reads file contents with line number prefixes.

Permission: read (auto-execute, no user confirmation required).
"""

from pathlib import Path

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def read_file(file_path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read a file from the local filesystem.

    Args:
        file_path: Absolute path to the file.
        offset: Starting line number (0-indexed).
        limit: Maximum number of lines to read (1-2000).

    Returns:
        File content with line number prefixes, or error message.
    """
    path = Path(file_path).resolve()

    if not path.exists():
        return f"[ERROR] File not found: {file_path}"
    if not path.is_file():
        return f"[ERROR] Path is a directory, not a file: {file_path}"

    # Check file size
    try:
        size = path.stat().st_size
        if size > MAX_FILE_SIZE:
            return f"[ERROR] File exceeds size limit (100MB): {file_path} ({size // (1024*1024)}MB)"
    except OSError as e:
        return f"[ERROR] Cannot access file: {file_path} — {e}"

    # Detect binary
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return f"[ERROR] Binary file detected (null bytes found): {file_path}"
    except OSError as e:
        return f"[ERROR] Permission denied: {file_path} — {e}"

    # Read file
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return f"[ERROR] Cannot decode file as UTF-8: {file_path}"
    except OSError as e:
        return f"[ERROR] Permission denied: {file_path} — {e}"

    total_lines = len(lines)
    if offset >= total_lines:
        return f"(File is {total_lines} lines; offset {offset} is beyond end of file)"

    # Apply offset and limit
    end = min(offset + limit, total_lines)
    selected = lines[offset:end]

    # Format with line numbers
    result = []
    for i, line in enumerate(selected, start=offset + 1):
        result.append(f"{i}\t{line.rstrip()}")

    output = "\n".join(result)

    if end < total_lines:
        output += f"\n\n(Showing lines {offset+1}-{end} of {total_lines})"

    return output
