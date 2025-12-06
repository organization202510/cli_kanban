"""TUI update/input handler for Kanban board."""

from cli_kanban.model import TaskStatus
from .model import TuiModel, ViewMode


def handle_key_press(model: TuiModel, key: str) -> bool:
    """Handle keyboard input.
    
    Args:
        model: TUI model to update.
        key: Key pressed (can be char, 'left', 'right', 'up', 'down', 'enter', 'esc', etc).
        
    Returns:
        True if should quit, False otherwise.
    """
    # Global keys
    if key == "q" or key == "ctrl+c":
        if model.view_mode == ViewMode.BOARD:
            return True
    
    if key == "esc":
        if model.view_mode != ViewMode.BOARD:
            model.view_mode = ViewMode.BOARD
            model.text_input = ""
        else:
            return True

    # Mode-specific handling
    if model.view_mode == ViewMode.BOARD:
        return handle_board_keys(model, key)
    elif model.view_mode == ViewMode.ADD_TASK:
        return handle_add_task_keys(model, key)
    elif model.view_mode == ViewMode.EDIT_TASK:
        return handle_edit_task_keys(model, key)
    elif model.view_mode == ViewMode.EDIT_DESCRIPTION:
        return handle_edit_description_keys(model, key)
    elif model.view_mode == ViewMode.EDIT_TAGS:
        return handle_edit_tags_keys(model, key)
    elif model.view_mode == ViewMode.CONFIRM_DELETE:
        return handle_confirm_delete_keys(model, key)
    elif model.view_mode == ViewMode.HELP:
        return handle_help_keys(model, key)

    return False


def handle_board_keys(model: TuiModel, key: str) -> bool:
    """Handle keys in board view mode."""
    if key == "left" or key == "h":
        model.navigate_left()
    elif key == "right" or key == "l":
        model.navigate_right()
    elif key == "up" or key == "k":
        model.navigate_up()
    elif key == "down" or key == "j":
        model.navigate_down()
    elif key == "a":
        model.view_mode = ViewMode.ADD_TASK
        model.text_input = ""
    elif key == "e" or key == "enter":
        task = model.get_current_task()
        if task:
            model.view_mode = ViewMode.EDIT_TASK
            model.text_input = task.title
    elif key == "d" or key == "delete":
        task = model.get_current_task()
        if task:
            model.pending_delete_id = task.id
            model.view_mode = ViewMode.CONFIRM_DELETE
    elif key == "m":
        task = model.get_current_task()
        if task:
            next_column = (model.current_column + 1) % len(model.columns)
            model.current_column = next_column
            model.follow_task_id = task.id
            model.move_task(task, next_column)
    elif key == "i":
        task = model.get_current_task()
        if task:
            model.view_mode = ViewMode.EDIT_DESCRIPTION
            model.text_input = task.description
    elif key == "t":
        task = model.get_current_task()
        if task:
            model.view_mode = ViewMode.EDIT_TAGS
            model.text_input = ", ".join(task.tags)
    elif key == "?":
        model.view_mode = ViewMode.HELP

    return False


def handle_add_task_keys(model: TuiModel, key: str) -> bool:
    """Handle keys in add task mode."""
    if key == "enter":
        if model.text_input.strip():
            status = model.columns[model.current_column].status
            model.create_task(model.text_input.strip(), status)
            model.view_mode = ViewMode.BOARD
            model.text_input = ""
    elif key == "esc":
        model.view_mode = ViewMode.BOARD
        model.text_input = ""
    elif key == "backspace":
        model.text_input = model.text_input[:-1]
    elif len(key) == 1 and ord(key) >= 32:  # Printable character
        model.text_input += key

    return False


def handle_edit_task_keys(model: TuiModel, key: str) -> bool:
    """Handle keys in edit task mode."""
    if key == "enter":
        if model.text_input.strip():
            task = model.get_current_task()
            if task:
                model.update_task_title(task.id, model.text_input.strip())
                model.view_mode = ViewMode.BOARD
                model.text_input = ""
    elif key == "esc":
        model.view_mode = ViewMode.BOARD
        model.text_input = ""
    elif key == "backspace":
        model.text_input = model.text_input[:-1]
    elif len(key) == 1 and ord(key) >= 32:  # Printable character
        model.text_input += key

    return False


def handle_edit_description_keys(model: TuiModel, key: str) -> bool:
    """Handle keys in edit description mode."""
    if key == "ctrl+s":
        task = model.get_current_task()
        if task:
            model.update_task_description(task.id, model.text_input)
            model.view_mode = ViewMode.BOARD
            model.text_input = ""
    elif key == "esc":
        model.view_mode = ViewMode.BOARD
        model.text_input = ""
    elif key == "backspace":
        model.text_input = model.text_input[:-1]
    elif key == "enter":
        model.text_input += "\n"
    elif len(key) == 1 and ord(key) >= 32:  # Printable character
        model.text_input += key

    return False


def handle_edit_tags_keys(model: TuiModel, key: str) -> bool:
    """Handle keys in edit tags mode."""
    if key == "enter":
        task = model.get_current_task()
        if task:
            tags = parse_tags_input(model.text_input)
            model.update_task_tags(task.id, tags)
            model.view_mode = ViewMode.BOARD
            model.text_input = ""
    elif key == "esc":
        model.view_mode = ViewMode.BOARD
        model.text_input = ""
    elif key == "backspace":
        model.text_input = model.text_input[:-1]
    elif len(key) == 1 and ord(key) >= 32:  # Printable character
        model.text_input += key

    return False


def handle_confirm_delete_keys(model: TuiModel, key: str) -> bool:
    """Handle keys in delete confirmation mode."""
    if key == "y":
        model.delete_task(model.pending_delete_id)
        model.pending_delete_id = 0
        model.view_mode = ViewMode.BOARD
    elif key == "n" or key == "esc":
        model.pending_delete_id = 0
        model.view_mode = ViewMode.BOARD

    return False


def handle_help_keys(model: TuiModel, key: str) -> bool:
    """Handle keys in help mode."""
    model.view_mode = ViewMode.BOARD
    return False


def parse_tags_input(input_str: str) -> list:
    """Parse comma-separated tags input."""
    tags = []
    for tag in input_str.split(","):
        tag = tag.strip().lower()
        if tag:
            tags.append(tag)
    return tags
