"""Skills management service.

Handles scanning, installing, and uninstalling SKILL.md files from
the .claude/skills/ directory. Skills are Markdown files with optional
YAML frontmatter containing 'name' and 'description' fields.
"""

import re
import shutil
from pathlib import Path

SKILLS_DIR = Path.cwd() / ".claude" / "skills"


def _ensure_skills_dir() -> Path:
    """Create skills directory if it doesn't exist."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    return SKILLS_DIR


def _parse_skill_md(filepath: Path) -> dict:
    """Parse a SKILL.md file and extract name + description.

    Looks for YAML frontmatter (--- ... ---) or falls back to
    first # heading as name and first paragraph as description.
    """
    result = {"name": filepath.stem, "description": "", "path": str(filepath)}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return result

    # Try YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        frontmatter = fm_match.group(1)
        for line in frontmatter.split("\n"):
            line = line.strip()
            if line.startswith("name:"):
                result["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                result["description"] = line.split(":", 1)[1].strip()
    else:
        # Fallback: first # heading as name
        heading = re.search(r"^#\s+(.+)", content, re.MULTILINE)
        if heading:
            result["name"] = heading.group(1).strip()

    # Use filename stem if name is empty
    if not result["name"]:
        result["name"] = filepath.stem

    return result


def list_skills() -> list[dict]:
    """Scan .claude/skills/ and return all installed skills."""
    skills_dir = _ensure_skills_dir()
    skills = []
    for filepath in sorted(skills_dir.glob("*.md")):
        skills.append(_parse_skill_md(filepath))
    return skills


def install_skill(source_path: str) -> dict | None:
    """Install a SKILL.md file from a given path.

    Returns the parsed skill info on success, or None on failure.
    Raises FileExistsError if a skill with the same filename already exists.
    """
    source = Path(source_path).resolve()
    if not source.exists():
        return None
    if not source.suffix.lower() == ".md":
        return None

    skills_dir = _ensure_skills_dir()
    dest = skills_dir / source.name

    if dest.exists():
        raise FileExistsError(f"Skill already exists: {source.name}. Uninstall it first.")

    shutil.copy2(source, dest)
    return _parse_skill_md(dest)


def uninstall_skill(name: str) -> bool:
    """Remove a skill by name (filename stem or frontmatter name).

    Returns True if a skill was removed, False if not found.
    """
    skills_dir = _ensure_skills_dir()
    for filepath in skills_dir.glob("*.md"):
        info = _parse_skill_md(filepath)
        if info["name"] == name or filepath.stem == name:
            filepath.unlink()
            return True
    return False
