"""Project context loading and conversation context compression.

Handles:
- Loading project configuration files (CLAUDE.md style)
- Token counting and context window management
- Automatic message summarization for long conversations
"""

import logging
from pathlib import Path

from src.models import Message, MessageRole, ProjectContext

logger = logging.getLogger(__name__)

# Approximate context limits
CONTEXT_WINDOW_TOKENS = 180000  # Conservative for most models
COMPRESSION_TRIGGER_RATIO = 0.7  # Start compressing at 70% of window
KEEP_RECENT_MESSAGES = 20  # Always keep most recent N messages fully intact


def load_project_context(project_dir: Path | None = None) -> ProjectContext:
    """Load project configuration from the working directory.

    Scans for CLAUDE.md or similar config files and extracts
    project metadata for the AI system prompt.
    """
    ctx = ProjectContext()
    if project_dir is None:
        project_dir = Path.cwd()

    ctx.project_name = project_dir.name

    # Scan for CLAUDE.md (root + immediate subdirectories)
    instructions_parts = []
    config_files = []

    root_md = project_dir / "CLAUDE.md"
    if root_md.exists():
        config_files.append(str(root_md))
        with open(root_md, "r", encoding="utf-8") as f:
            instructions_parts.append(f.read())

    # Also scan immediate subdirectories (max depth 1)
    try:
        for sub in sorted(project_dir.iterdir()):
            if sub.is_dir() and not sub.name.startswith("."):
                sub_md = sub / "CLAUDE.md"
                if sub_md.exists():
                    config_files.append(str(sub_md))
                    with open(sub_md, "r", encoding="utf-8") as f:
                        instructions_parts.append(f"## From {sub.name}/\n{f.read()}")
    except PermissionError:
        pass

    if config_files:
        ctx.config_file_path = ", ".join(config_files)
        ctx.instructions = "\n\n".join(instructions_parts)

    # Detect tech stack from common files
    ctx.tech_stack = _detect_tech_stack(project_dir)
    ctx.directory_structure = _summarize_directory(project_dir)

    return ctx


def _detect_tech_stack(project_dir: Path) -> list[str]:
    """Detect technology stack from project files."""
    stack = []
    indicators = {
        "pyproject.toml": "Python",
        "requirements.txt": "Python",
        "package.json": "Node.js",
        "tsconfig.json": "TypeScript",
        "go.mod": "Go",
        "Cargo.toml": "Rust",
        "Gemfile": "Ruby",
        "composer.json": "PHP",
        "pom.xml": "Java/Maven",
        "build.gradle": "Java/Gradle",
        "CMakeLists.txt": "C/C++",
    }
    for filename, tech in indicators.items():
        if (project_dir / filename).exists():
            stack.append(tech)

    return stack or ["Unknown"]


def _summarize_directory(project_dir: Path, max_depth: int = 2) -> dict:
    """Generate a summary of the project directory structure."""
    summary: dict = {"root": str(project_dir), "top_level": []}
    try:
        for item in sorted(project_dir.iterdir()):
            if item.name.startswith(".") and item.name not in (".gitignore",):
                continue
            if item.is_dir():
                contents = []
                try:
                    for sub in sorted(item.iterdir()):
                        if not sub.name.startswith("."):
                            contents.append(sub.name)
                except PermissionError:
                    pass
                summary["top_level"].append({
                    "name": item.name,
                    "type": "dir",
                    "contents": contents[:10],
                })
            else:
                summary["top_level"].append({
                    "name": item.name,
                    "type": "file",
                })
    except PermissionError:
        pass
    return summary


def estimate_tokens(text: str) -> int:
    """Rough token count estimation. ~4 characters per token."""
    return max(1, len(text) // 4)


def estimate_session_tokens(messages: list[Message]) -> int:
    """Estimate total tokens used by conversation messages."""
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.content)
        for tc in msg.tool_calls:
            total += estimate_tokens(str(tc.parameters))
            if tc.result:
                total += estimate_tokens(tc.result)
    return total


def get_compress_threshold_tokens() -> int:
    """Get the token count at which compression should trigger.

    Reads COMPRESSION_THRESHOLD from config.txt (default 0.7).
    """
    from src.config import get_compression_threshold
    ratio = get_compression_threshold()
    return int(CONTEXT_WINDOW_TOKENS * ratio)


def should_compress(messages: list[Message]) -> bool:
    """Check if the conversation should be compressed."""
    tokens = estimate_session_tokens(messages)
    return tokens > get_compress_threshold_tokens()


def _summarize_with_llm(messages: list[Message]) -> str:
    """Use LangChain + LLM to generate a real AI summary of conversation messages.

    Calls the LLM (via DeepSeek proxy) to produce a concise, accurate summary
    of the provided messages. Much higher quality than keyword extraction.
    """
    from src.config import get_api_key, get_base_url, get_model
    from langchain_anthropic import ChatAnthropic
    from langchain.chains.summarize import load_summarize_chain
    from langchain.schema import Document

    # Build LangChain LLM with DeepSeek proxy
    llm = ChatAnthropic(
        model=get_model(),
        api_key=get_api_key(),
        base_url=get_base_url(),
        max_tokens=1024,
        temperature=0,
    )

    # Convert messages to LangChain Documents
    docs = []
    for msg in messages:
        role_label = {
            MessageRole.USER: "User",
            MessageRole.ASSISTANT: "AI",
            MessageRole.SYSTEM: "System",
        }.get(msg.role, msg.role.value)
        text = f"[{role_label}]: {msg.content[:800]}"
        if msg.tool_calls:
            tool_names = [tc.tool_name for tc in msg.tool_calls]
            text += f"\n(Tools used: {', '.join(tool_names)})"
        docs.append(Document(page_content=text))

    # Use LangChain's stuff summarize chain
    chain = load_summarize_chain(llm, chain_type="stuff", verbose=False)
    result = chain.invoke({"input_documents": docs})

    return result.get("output_text", "") if isinstance(result, dict) else str(result)


def compress_messages(messages: list[Message]) -> list[Message]:
    """Compress conversation context using LangChain LLM summarization.

    Keeps the most recent KEEP_RECENT_MESSAGES fully intact.
    Pinned messages are preserved and never compressed.
    Early non-pinned messages are summarized via LLM for accurate compression.
    """
    if len(messages) <= KEEP_RECENT_MESSAGES:
        return messages

    split_point = len(messages) - KEEP_RECENT_MESSAGES
    early = messages[:split_point]
    recent = messages[split_point:]

    # Separate pinned messages — they survive compression
    pinned = [m for m in early if m.pinned]
    compressible = [m for m in early if not m.pinned]

    if not compressible:
        return messages  # Nothing to compress

    # Use LangChain LLM for real summarization
    try:
        summary_text = _summarize_with_llm(compressible)
    except Exception as e:
        logger.warning("LLM summarization failed, falling back: %s", e)
        summary_text = _fallback_summary(compressible)

    summary_msg = Message(
        role=MessageRole.SYSTEM,
        content=f"[Conversation history summary]\n\n{summary_text}",
    )

    return pinned + [summary_msg] + recent


def _fallback_summary(messages: list[Message]) -> str:
    """Fallback: extract key points without LLM if summarization fails."""
    topics = []
    for msg in messages:
        if msg.role == MessageRole.USER and msg.content.strip():
            first = msg.content.strip().split(".")[0][:120]
            if first:
                topics.append(first)
    return "Topics: " + "; ".join(topics[-10:]) if topics else "(no user messages)"
