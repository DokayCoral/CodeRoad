"""Grep tool: regex search across file contents.

Permission: read (auto-execute, no user confirmation required).
"""

import re
from pathlib import Path


def grep_search(
    pattern: str,
    path_str: str = ".",
    glob: str | None = None,
    output_mode: str = "content",
    context: int = 0,
    case_insensitive: bool = False,
    head_limit: int = 250,
    multiline: bool = False,
) -> str:
    """Search file contents using regular expressions.

    Args:
        pattern: Regular expression pattern to search for.
        path_str: File or directory to search (default: current directory).
        glob: File pattern filter (e.g., "*.py").
        output_mode: "content" (default), "files_with_matches", or "count".
        context: Lines of context around matches (max 10).
        case_insensitive: Case-insensitive search (-i flag).
        head_limit: Max results (default 250).
        multiline: Enable multiline mode.

    Returns:
        Search results in the requested output mode.
    """
    search_path = Path(path_str).resolve()
    if not search_path.exists():
        return f"[ERROR] Path not found: {path_str}"

    # Compile regex
    try:
        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.DOTALL
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"[ERROR] Invalid regular expression: {pattern}. {e}"

    # Collect files to search
    files = []
    if search_path.is_file():
        files = [search_path]
    else:
        glob_pattern = glob or "*"
        for p in search_path.rglob(glob_pattern):
            if p.is_file():
                # Skip common directories to ignore
                if any(part.startswith(".") for part in p.parts):
                    continue
                if any(part in ("node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build")
                       for part in p.parts):
                    continue
                files.append(p)

    if not files:
        return "No files matched search criteria."

    # Search
    match_count = 0
    file_matches: dict[str, list[str]] = {}
    file_counts: dict[str, int] = {}

    for file_path in files:
        # Skip binary
        try:
            with open(file_path, "rb") as f:
                if b"\x00" in f.read(8192):
                    continue
        except OSError:
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            continue

        file_counts[str(file_path)] = 0

        for i, line in enumerate(lines):
            if regex.search(line):
                file_counts[str(file_path)] += 1
                match_count += 1
                if match_count > head_limit:
                    break

                if output_mode == "content":
                    rel_path = str(file_path)
                    if context > 0:
                        ctx_start = max(0, i - context)
                        ctx_end = min(len(lines), i + context + 1)
                        for ci in range(ctx_start, ctx_end):
                            prefix = ">" if ci == i else " "
                            key = f"{rel_path}:{ci+1}"
                            if key not in file_matches:
                                file_matches[key] = [f"{prefix} {rel_path}:{ci+1}: {lines[ci].rstrip()}"]
                    else:
                        entry = f"{rel_path}:{i+1}: {line.rstrip()}"
                        if rel_path not in file_matches:
                            file_matches[rel_path] = []
                        file_matches[rel_path].append(entry)

        if match_count > head_limit:
            break

    # Format output
    if output_mode == "files_with_matches":
        matched_files = [f for f, c in file_counts.items() if c > 0]
        if not matched_files:
            return "No matches found."
        return "\n".join(matched_files)

    if output_mode == "count":
        lines_out = []
        for f, c in sorted(file_counts.items()):
            if c > 0:
                lines_out.append(f"{f}: {c} matches")
        if not lines_out:
            return "No matches found."
        return "\n".join(lines_out)

    # content mode (default)
    if not file_matches:
        return "No matches found."

    result = []
    for key in sorted(file_matches.keys()):
        result.extend(file_matches[key])

    output = "\n".join(result[:head_limit])
    if match_count > head_limit:
        output += f"\n\n(Results truncated at {head_limit}; {match_count} total matches)"
    return output
