#!/usr/bin/env python3
"""Test script to verify CLI Kanban functionality."""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from cli_kanban.db import DB
from cli_kanban.model import TaskStatus, get_all_columns
from cli_kanban.tui import TuiModel
from cli_kanban.tui.view import render_board


def test_database():
    """Test database operations."""
    print("🧪 Testing Database Operations...")
    
    # Create a test database
    db_path = "test_db.sqlite"
    db = DB(db_path)
    
    # Test create
    print("  ✓ Creating tasks...")
    t1 = db.create_task("Task 1", TaskStatus.TODO)
    t2 = db.create_task("Task 2", TaskStatus.IN_PROGRESS)
    t3 = db.create_task("Task 3", TaskStatus.DONE)
    
    # Test read
    print("  ✓ Reading all tasks...")
    all_tasks = db.get_all_tasks()
    assert len(all_tasks) == 3, "Should have 3 tasks"
    
    # Test update
    print("  ✓ Updating task...")
    db.update_task(t1.id, "Updated Task 1", TaskStatus.IN_PROGRESS)
    
    # Test delete
    print("  ✓ Deleting task...")
    db.delete_task(t3.id)
    all_tasks = db.get_all_tasks()
    assert len(all_tasks) == 2, "Should have 2 tasks after delete"
    
    db.close()
    Path(db_path).unlink()
    print("✅ Database tests passed!\n")


def test_model():
    """Test TaskStatus and Column models."""
    print("🧪 Testing Models...")
    
    # Test TaskStatus workflow
    print("  ✓ Testing TaskStatus workflow...")
    assert TaskStatus.TODO.next() == TaskStatus.IN_PROGRESS
    assert TaskStatus.IN_PROGRESS.next() == TaskStatus.DONE
    assert TaskStatus.DONE.prev() == TaskStatus.IN_PROGRESS
    assert TaskStatus.IN_PROGRESS.prev() == TaskStatus.TODO
    
    # Test columns
    print("  ✓ Testing columns...")
    columns = get_all_columns()
    assert len(columns) == 3, "Should have 3 columns"
    assert columns[0].status == TaskStatus.TODO
    assert columns[1].status == TaskStatus.IN_PROGRESS
    assert columns[2].status == TaskStatus.DONE
    
    print("✅ Model tests passed!\n")


def test_tui_model():
    """Test TUI model."""
    print("🧪 Testing TUI Model...")
    
    # Create test database
    db_path = "test_tui_db.sqlite"
    db = DB(db_path)
    
    # Add some tasks
    db.create_task("Test 1", TaskStatus.TODO)
    db.create_task("Test 2", TaskStatus.IN_PROGRESS)
    
    # Test TUI model
    print("  ✓ Creating TUI model...")
    model = TuiModel(db=db)
    model.load_tasks()
    
    print("  ✓ Testing navigation...")
    model.navigate_right()
    assert model.current_column == 1
    model.navigate_left()
    assert model.current_column == 0
    
    print("  ✓ Testing task operations...")
    model.create_task("New task", TaskStatus.TODO)
    
    db.close()
    Path(db_path).unlink()
    print("✅ TUI model tests passed!\n")


def test_rendering():
    """Test rendering."""
    print("🧪 Testing Rendering...")
    
    # Create test database with demo data
    db_path = "test_render_db.sqlite"
    db = DB(db_path)
    
    db.create_task("设计数据库", TaskStatus.DONE)
    db.create_task("实现功能", TaskStatus.IN_PROGRESS)
    db.create_task("编写测试", TaskStatus.TODO)
    
    model = TuiModel(db=db)
    model.load_tasks()
    
    print("  ✓ Rendering board...")
    view = render_board(model)
    assert "📋 Kanban Board" in view
    assert "Todo" in view
    assert "In Progress" in view
    assert "Done" in view
    
    db.close()
    Path(db_path).unlink()
    print("✅ Rendering tests passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("CLI Kanban - Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_model()
        test_database()
        test_tui_model()
        test_rendering()
        
        print("=" * 60)
        print("🎉 All tests passed successfully!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
