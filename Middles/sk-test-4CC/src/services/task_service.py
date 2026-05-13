"""Task service: task lifecycle management and dependency resolution.

Handles creating, updating, and tracking tasks within a session.
"""

from datetime import datetime
from typing import Optional

from src.models import Task, TaskStatus


def create_task(title: str, description: str = "", dependencies: list[str] | None = None) -> Task:
    """Create a new task."""
    return Task(
        title=title,
        description=description,
        dependencies=list(dependencies) if dependencies else [],
    )


def start_task(task: Task, all_tasks: list[Task]) -> str:
    """Move a task to in_progress status.

    Returns error message if task is blocked, or success message.
    """
    if task.status == TaskStatus.COMPLETED:
        return f"Task '{task.title}' is already completed"
    if task.status == TaskStatus.CANCELLED:
        return f"Task '{task.title}' is cancelled"

    if task.is_blocked(all_tasks):
        blocked_by = []
        task_map = {t.id: t for t in all_tasks}
        for dep_id in task.dependencies:
            dep = task_map.get(dep_id)
            if dep and dep.status != TaskStatus.COMPLETED:
                blocked_by.append(dep.title)
        return f"Task '{task.title}' is blocked by: {', '.join(blocked_by)}"

    task.status = TaskStatus.IN_PROGRESS
    return f"Task '{task.title}' started"


def complete_task(task: Task, all_tasks: list[Task]) -> str:
    """Mark a task as completed.

    Returns success message listing newly unblocked tasks.
    """
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()

    # Find tasks that are now unblocked
    newly_unblocked = []
    task_map = {t.id: t for t in all_tasks}
    for t in all_tasks:
        if t.id == task.id:
            continue
        if t.status == TaskStatus.PENDING:
            if task.id in t.dependencies:
                if not t.is_blocked(all_tasks):
                    newly_unblocked.append(t.title)

    msg = f"Task '{task.title}' completed"
    if newly_unblocked:
        msg += f"\nUnblocked tasks: {', '.join(newly_unblocked)}"
    return msg


def cancel_task(task: Task) -> str:
    """Cancel a task."""
    if task.status == TaskStatus.COMPLETED:
        return f"Task '{task.title}' is already completed"
    task.status = TaskStatus.CANCELLED
    return f"Task '{task.title}' cancelled"


def parse_tasks_from_text(text: str) -> list[Task]:
    """Parse a task list from AI-generated text.

    Looks for lines like '- [ ] Task title' or numbered lists.
    """
    tasks = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Markdown checkbox format: - [ ] Title
        if line.startswith("- [ ]"):
            title = line[5:].strip()
            if title:
                tasks.append(create_task(title=title))
        # Numbered: 1. Title
        elif line and line[0].isdigit() and ". " in line:
            title = line.split(". ", 1)[1].strip()
            if title:
                tasks.append(create_task(title=title))
    return tasks
