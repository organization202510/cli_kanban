"""SQLite database implementation for Kanban board."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from cli_kanban.model import Task, TaskStatus


class DB:
    """SQLite database connection and operations."""

    def __init__(self, db_path: str):
        """Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on status
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)
        
        # Migration: add description column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN description TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Migration: add tags column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN tags TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def create_task(self, title: str, status: TaskStatus = TaskStatus.TODO) -> Task:
        """Create a new task.
        
        Args:
            title: Task title.
            status: Task status (default: TODO).
            
        Returns:
            Created task object.
        """
        cursor = self.conn.cursor()
        now = datetime.now()
        
        cursor.execute(
            """INSERT INTO tasks (title, description, tags, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, "", "", status.value, now, now)
        )
        self.conn.commit()
        
        task_id = cursor.lastrowid
        return Task(
            id=task_id,
            title=title,
            description="",
            tags=[],
            status=status,
            created_at=now,
            updated_at=now
        )

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all tasks.
        
        Returns:
            List of all tasks ordered by creation date (newest first).
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, title, description, tags, status, created_at, updated_at
               FROM tasks ORDER BY created_at DESC"""
        )
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(self._row_to_task(row))
        return tasks

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Retrieve tasks by status.
        
        Args:
            status: Task status to filter by.
            
        Returns:
            List of tasks with given status ordered by creation date (newest first).
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, title, description, tags, status, created_at, updated_at
               FROM tasks WHERE status = ? ORDER BY created_at DESC""",
            (status.value,)
        )
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(self._row_to_task(row))
        return tasks

    def update_task(self, task_id: int, title: str, status: TaskStatus) -> None:
        """Update a task.
        
        Args:
            task_id: Task ID to update.
            title: New task title.
            status: New task status.
            
        Raises:
            ValueError: If task not found.
        """
        cursor = self.conn.cursor()
        now = datetime.now()
        
        cursor.execute(
            """UPDATE tasks SET title = ?, status = ?, updated_at = ? WHERE id = ?""",
            (title, status.value, now, task_id)
        )
        self.conn.commit()
        
        if cursor.rowcount == 0:
            raise ValueError(f"Task {task_id} not found")

    def update_task_status(self, task_id: int, status: TaskStatus) -> None:
        """Update only the status of a task.
        
        Args:
            task_id: Task ID to update.
            status: New task status.
            
        Raises:
            ValueError: If task not found.
        """
        cursor = self.conn.cursor()
        now = datetime.now()
        
        cursor.execute(
            """UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?""",
            (status.value, now, task_id)
        )
        self.conn.commit()
        
        if cursor.rowcount == 0:
            raise ValueError(f"Task {task_id} not found")

    def update_task_description(self, task_id: int, description: str) -> None:
        """Update only the description of a task.
        
        Args:
            task_id: Task ID to update.
            description: New task description.
            
        Raises:
            ValueError: If task not found.
        """
        cursor = self.conn.cursor()
        now = datetime.now()
        
        cursor.execute(
            """UPDATE tasks SET description = ?, updated_at = ? WHERE id = ?""",
            (description, now, task_id)
        )
        self.conn.commit()
        
        if cursor.rowcount == 0:
            raise ValueError(f"Task {task_id} not found")

    def update_task_tags(self, task_id: int, tags: List[str]) -> None:
        """Update only the tags of a task.
        
        Args:
            task_id: Task ID to update.
            tags: List of tags.
            
        Raises:
            ValueError: If task not found.
        """
        cursor = self.conn.cursor()
        now = datetime.now()
        tags_str = self._tags_to_string(tags)
        
        cursor.execute(
            """UPDATE tasks SET tags = ?, updated_at = ? WHERE id = ?""",
            (tags_str, now, task_id)
        )
        self.conn.commit()
        
        if cursor.rowcount == 0:
            raise ValueError(f"Task {task_id} not found")

    def delete_task(self, task_id: int) -> None:
        """Delete a task.
        
        Args:
            task_id: Task ID to delete.
            
        Raises:
            ValueError: If task not found.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        
        if cursor.rowcount == 0:
            raise ValueError(f"Task {task_id} not found")

    @staticmethod
    def _parse_tags(tags_str: str) -> List[str]:
        """Parse comma-separated tags string to list.
        
        Args:
            tags_str: Comma-separated tags string.
            
        Returns:
            List of tags.
        """
        if not tags_str:
            return []
        
        tags = []
        seen = set()
        for tag in tags_str.split(","):
            tag = tag.strip().lower()
            if tag and tag not in seen:
                tags.append(tag)
                seen.add(tag)
        return tags

    @staticmethod
    def _tags_to_string(tags: List[str]) -> str:
        """Convert list of tags to comma-separated string.
        
        Args:
            tags: List of tags.
            
        Returns:
            Comma-separated tags string.
        """
        cleaned = []
        seen = set()
        for tag in tags:
            tag = tag.strip().lower()
            if tag and tag not in seen:
                cleaned.append(tag)
                seen.add(tag)
        return ",".join(cleaned)

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        """Convert database row to Task object.
        
        Args:
            row: Database row.
            
        Returns:
            Task object.
        """
        tags = DB._parse_tags(row["tags"])
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            tags=tags,
            status=TaskStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
