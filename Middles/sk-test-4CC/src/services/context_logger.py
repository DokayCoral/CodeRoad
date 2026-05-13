"""Context event logger — records key context management events to a JSONL file.

Provides user-verifiable audit trail of: session save/load, context compression,
project context loading. Events are written as one JSON object per line.
"""

import json
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude-code-clone" / "context.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB rotation threshold


def _ensure_log_dir() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def _rotate_if_needed() -> None:
    """Truncate log if over size limit."""
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
        # Keep last 1MB worth of lines
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        keep_size = 1 * 1024 * 1024
        while lines and sum(len(l) for l in lines) > keep_size:
            lines.pop(0)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)


def _log_event(event_type: str, data: dict) -> None:
    """Append a JSON log line."""
    _ensure_log_dir()
    _rotate_if_needed()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        **data,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_session_saved(msg_count: int, token_count: int, file_path: str) -> None:
    _log_event("SESSION_SAVED", {
        "msg_count": msg_count,
        "token_count": token_count,
        "file": file_path,
    })


def log_session_loaded(session_id: str, msg_count: int) -> None:
    _log_event("SESSION_LOADED", {
        "session_id": session_id,
        "msg_count": msg_count,
    })


def log_context_compressed(before_msgs: int, after_msgs: int,
                           before_tokens: int, after_tokens: int) -> None:
    _log_event("CONTEXT_COMPRESSED", {
        "before": {"msgs": before_msgs, "tokens": before_tokens},
        "after": {"msgs": after_msgs, "tokens": after_tokens},
    })


def log_project_context_loaded(source_file: str, tech_stack: list[str],
                               instructions_len: int) -> None:
    _log_event("PROJECT_CONTEXT_LOADED", {
        "source": source_file,
        "tech_stack": tech_stack,
        "instructions_len": instructions_len,
    })
