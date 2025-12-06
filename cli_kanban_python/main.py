"""Main entry point for CLI Kanban."""

import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: click is not installed. Please run: pip install -r requirements.txt")
    sys.exit(1)

from cli_kanban.db import DB
from cli_kanban.tui import TuiModel, ViewMode, handle_key_press
from cli_kanban.tui.view import (
    render_board,
    render_add_task,
    render_edit_task,
    render_edit_description,
    render_edit_tags,
    render_confirm_delete,
    render_help,
)


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def render_view(model: TuiModel) -> str:
    """Render the current view based on view mode."""
    if model.view_mode == ViewMode.ADD_TASK:
        return render_add_task(model)
    elif model.view_mode == ViewMode.EDIT_TASK:
        return render_edit_task(model)
    elif model.view_mode == ViewMode.EDIT_DESCRIPTION:
        return render_edit_description(model)
    elif model.view_mode == ViewMode.EDIT_TAGS:
        return render_edit_tags(model)
    elif model.view_mode == ViewMode.CONFIRM_DELETE:
        return render_confirm_delete(model)
    elif model.view_mode == ViewMode.HELP:
        return render_help(model)
    else:
        return render_board(model)


def run_tui(database: DB):
    """Run the TUI application in demo mode."""
    # Initialize model
    model = TuiModel(db=database)
    model.load_tasks()
    
    # Simple demo mode - show the board
    try:
        while True:
            clear_screen()
            view = render_view(model)
            print(view)
            print("\n" + "=" * 80)
            print("Enter command: ", end="", flush=True)
            
            try:
                cmd = input().strip().lower()
                if cmd == "q":
                    break
                if cmd:
                    # Convert single char to full command for handle_key_press
                    if handle_key_press(model, cmd):
                        break
                model.current_time = datetime.now()
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\n")
    finally:
        clear_screen()


@click.command()
@click.option(
    "-d",
    "--db",
    "db_path",
    type=click.Path(),
    default=None,
    help="Path to SQLite database file",
)
def main(db_path: str):
    """CLI Kanban - A terminal-based Kanban board management tool."""
    # Get default database path if not specified
    if not db_path:
        home_dir = Path.home()
        db_path = home_dir / ".cli_kanban.db"
    else:
        db_path = Path(db_path)

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize database
        database = DB(str(db_path))

        # Run TUI
        run_tui(database)

        # Close database
        database.close()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
