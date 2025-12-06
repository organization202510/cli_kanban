"""TUI model and event handlers for Kanban board."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from cli_kanban.db import DB
from cli_kanban.model import Column, Task, TaskStatus, get_all_columns


class ViewMode(Enum):
    """TUI view modes."""
    BOARD = "board"
    ADD_TASK = "add_task"
    EDIT_TASK = "edit_task"
    EDIT_DESCRIPTION = "edit_description"
    EDIT_TAGS = "edit_tags"
    CONFIRM_DELETE = "confirm_delete"
    HELP = "help"


@dataclass
class TuiModel:
    """Main TUI model."""
    db: DB
    current_column: int = 0
    current_task: int = 0
    scroll_offsets: List[int] = field(default_factory=lambda: [0, 0, 0])
    view_mode: ViewMode = ViewMode.BOARD
    pending_delete_id: int = 0
    follow_task_id: int = 0
    text_input: str = ""
    width: int = 120
    height: int = 30
    error: Optional[str] = None
    columns: List[Column] = field(default_factory=get_all_columns)
    current_time: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Initialize after dataclass creation."""
        pass

    def load_tasks(self) -> None:
        """Load all tasks from database."""
        try:
            tasks = self.db.get_all_tasks()
            self.organize_tasks(tasks)
            self.error = None
        except Exception as e:
            self.error = str(e)

    def organize_tasks(self, tasks: List[Task]) -> None:
        """Organize tasks into columns by status."""
        # Reset all columns
        for col in self.columns:
            col.tasks = []

        # Organize tasks by status
        for task in tasks:
            for col in self.columns:
                if col.status == task.status:
                    col.tasks.append(task)
                    break

        # If we're following a task after move, find its position
        if self.follow_task_id != 0:
            found = False
            for i, task in enumerate(self.columns[self.current_column].tasks):
                if task.id == self.follow_task_id:
                    self.current_task = i
                    found = True
                    break
            self.follow_task_id = 0
            if found:
                self.ensure_task_visible()
                return

        # Ensure current_task is within bounds
        col_tasks = self.columns[self.current_column].tasks
        if self.current_task >= len(col_tasks):
            self.current_task = max(0, len(col_tasks) - 1)
        if self.current_task < 0:
            self.current_task = 0

    def get_current_task(self) -> Optional[Task]:
        """Get the currently selected task."""
        col = self.columns[self.current_column]
        if len(col.tasks) == 0 or self.current_task >= len(col.tasks):
            return None
        return col.tasks[self.current_task]

    def ensure_task_visible(self) -> None:
        """Adjust scroll offset to keep current task visible."""
        MAX_VISIBLE_TASKS = 10
        offset = self.scroll_offsets[self.current_column]

        # If current task is above visible area, scroll up
        if self.current_task < offset:
            self.scroll_offsets[self.current_column] = self.current_task

        # If current task is below visible area, scroll down
        if self.current_task >= offset + MAX_VISIBLE_TASKS:
            self.scroll_offsets[self.current_column] = self.current_task - MAX_VISIBLE_TASKS + 1

    def navigate_left(self) -> None:
        """Navigate to the left column."""
        if self.current_column > 0:
            self.current_column -= 1
            self.current_task = 0

    def navigate_right(self) -> None:
        """Navigate to the right column."""
        if self.current_column < len(self.columns) - 1:
            self.current_column += 1
            self.current_task = 0

    def navigate_up(self) -> None:
        """Navigate to the task above."""
        if self.current_task > 0:
            self.current_task -= 1
            self.ensure_task_visible()

    def navigate_down(self) -> None:
        """Navigate to the task below."""
        col = self.columns[self.current_column]
        if self.current_task < len(col.tasks) - 1:
            self.current_task += 1
            self.ensure_task_visible()

    def create_task(self, title: str, status: TaskStatus) -> None:
        """Create a new task."""
        try:
            self.db.create_task(title, status)
            self.load_tasks()
            self.error = None
        except Exception as e:
            self.error = str(e)

    def update_task_title(self, task_id: int, title: str) -> None:
        """Update a task's title."""
        try:
            task = self.get_current_task()
            if task:
                self.db.update_task(task_id, title, task.status)
                self.load_tasks()
                self.error = None
        except Exception as e:
            self.error = str(e)

    def update_task_description(self, task_id: int, description: str) -> None:
        """Update a task's description."""
        try:
            self.db.update_task_description(task_id, description)
            self.load_tasks()
            self.error = None
        except Exception as e:
            self.error = str(e)

    def update_task_tags(self, task_id: int, tags: List[str]) -> None:
        """Update a task's tags."""
        try:
            self.db.update_task_tags(task_id, tags)
            self.load_tasks()
            self.error = None
        except Exception as e:
            self.error = str(e)

    def delete_task(self, task_id: int) -> None:
        """Delete a task."""
        try:
            self.db.delete_task(task_id)
            self.load_tasks()
            self.error = None
        except Exception as e:
            self.error = str(e)

    def move_task(self, task: Task, target_column: int) -> None:
        """Move a task to target column."""
        try:
            new_status = self.columns[target_column].status
            self.db.update_task_status(task.id, new_status)
            self.load_tasks()
            self.error = None
        except Exception as e:
            self.error = str(e)
