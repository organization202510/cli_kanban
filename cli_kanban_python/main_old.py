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
    """Run the TUI application."""
    # Initialize model
    model = TuiModel(db=database)
    model.load_tasks()

    # Try using curses for better Unix terminal handling
    if not ON_WINDOWS and HAS_UNIX_TERM:
        try:
            import curses

            def main(stdscr):
                curses.cbreak()
                stdscr.keypad(True)
                stdscr.nodelay(True)

                while True:
                    try:
                        # Clear and render
                        stdscr.clear()
                        view = render_view(model)
                        stdscr.addstr(view)
                        stdscr.refresh()

                        # Update time
                        model.current_time = datetime.now()

                        # Get input with timeout
                        stdscr.timeout(100)
                        try:
                            ch = stdscr.getch()
                            if ch == -1:  # Timeout
                                continue
                            elif ch == curses.KEY_UP:
                                key = "up"
                            elif ch == curses.KEY_DOWN:
                                key = "down"
                            elif ch == curses.KEY_LEFT:
                                key = "left"
                            elif ch == curses.KEY_RIGHT:
                                key = "right"
                            elif ch == curses.KEY_DC:
                                key = "delete"
                            elif ch == ord("q"):
                                key = "q"
                            elif ch == 27:  # Escape
                                key = "esc"
                            elif ch == ord("\n") or ch == ord("\r"):
                                key = "enter"
                            elif ch == curses.KEY_BACKSPACE or ch == 127:
                                key = "backspace"
                            elif ch == 19:  # Ctrl+S
                                key = "ctrl+s"
                            elif ch == 3:  # Ctrl+C
                                key = "ctrl+c"
                            elif 32 <= ch < 127:
                                key = chr(ch)
                            else:
                                continue

                            if handle_key_press(model, key):
                                break
                        except KeyboardInterrupt:
                            break
                    except Exception:
                        continue

            curses.wrapper(main)
            return
        except ImportError:
            pass

    # Fallback: Simple text-based interface for Windows and fallback
    terminal = TerminalReader()

    try:
        while True:
            clear_screen()
            view = render_view(model)
            print(view, flush=True)

            # Update time
            model.current_time = datetime.now()

            # Get input with short timeout
            if ON_WINDOWS:
                # Windows doesn't have non-blocking stdin, so we just try to read
                key = terminal.read_key()
            else:
                # Try non-blocking read on Unix
                time.sleep(0.01)
                key = terminal.read_key()

            if key != "unknown":
                if handle_key_press(model, key):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        terminal.cleanup()
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
