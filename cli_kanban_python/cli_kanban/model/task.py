"""Task model for Kanban board."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class TaskStatus(str, Enum):
    """Task status enumeration."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    def next(self) -> "TaskStatus":
        """Get the next status in workflow."""
        if self == TaskStatus.TODO:
            return TaskStatus.IN_PROGRESS
        elif self == TaskStatus.IN_PROGRESS:
            return TaskStatus.DONE
        else:
            return TaskStatus.DONE

    def prev(self) -> "TaskStatus":
        """Get the previous status in workflow."""
        if self == TaskStatus.DONE:
            return TaskStatus.IN_PROGRESS
        elif self == TaskStatus.IN_PROGRESS:
            return TaskStatus.TODO
        else:
            return TaskStatus.TODO


@dataclass
class Task:
    """Represents a Kanban task item."""
    id: int
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Column:
    """Represents a Kanban column."""
    name: str
    status: TaskStatus
    tasks: List[Task] = field(default_factory=list)


def get_all_columns() -> List[Column]:
    """Get all three columns in order."""
    return [
        Column(name="Todo", status=TaskStatus.TODO),
        Column(name="In Progress", status=TaskStatus.IN_PROGRESS),
        Column(name="Done", status=TaskStatus.DONE),
    ]
