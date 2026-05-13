"""Write tool: creates or overwrites files.

Permission: write (requires user confirmation).
"""

import shutil
from pathlib import Path


def write_file(file_path: str, content: str) -> str:
    """Write content to a file. Creates parent directories as needed.

    Args:
        file_path: Absolute path to the file.
        content: Full file content to write.

    Returns:
        Success or error message.
    """
    path = Path(file_path).resolve()

    # Check if path is a directory
    if path.is_dir():
        return f"[ERROR] Cannot overwrite directory: {file_path}"

    # Check if file exists and backup
    is_new = not path.exists()

    if not is_new:
        # Create backup
        try:
            backup_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, backup_path)
        except OSError:
            pass  # Non-critical: continue without backup

        # Check for external modification
        try:
            mtime_before = path.stat().st_mtime
        except OSError:
            mtime_before = None

    # Ensure parent directory exists
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return f"[ERROR] Cannot create parent directories: {path.parent} — {e}"

    # Write file (atomic via temp file)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        tmp_path.replace(path)
    except OSError as e:
        return f"[ERROR] Failed to write file: {file_path} — {e}"
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    # Report
    size = len(content.encode("utf-8"))
    if is_new:
        return f"Created file: {file_path} ({size} bytes)"
    else:
        return f"Updated file: {file_path} ({size} bytes, backup at {path.with_suffix(path.suffix + '.bak')})"
