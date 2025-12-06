"""TUI view rendering for Kanban board."""

from datetime import datetime
from typing import List
import re

try:
    from wcwidth import wcwidth, wcswidth
except Exception:
    # Fallback: simple width estimations if wcwidth not installed
    def wcwidth(ch):
        return 1 if ch and ord(ch) >= 32 else 0

    def wcswidth(s):
        return sum(wcwidth(ch) for ch in s)

from cli_kanban.model import Task, TaskStatus

# Regex to match ANSI escape sequences
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def visible_width(s: str) -> int:
    try:
        w = wcswidth(strip_ansi(s))
        return w if w >= 0 else len(strip_ansi(s))
    except Exception:
        return len(strip_ansi(s))


def truncate_ansi(s: str, max_width: int) -> str:
    """Truncate string s to max visible width, preserving ANSI sequences."""
    out = []
    cur = 0
    i = 0
    L = len(s)
    while i < L:
        if s[i] == "\x1b":
            # capture entire ANSI sequence until 'm'
            m_end = s.find("m", i)
            if m_end == -1:
                break
            out.append(s[i:m_end + 1])
            i = m_end + 1
            continue
        ch = s[i]
        w = wcwidth(ch)
        if w < 0:
            w = 0
        if cur + w > max_width:
            break
        out.append(ch)
        cur += w
        i += 1

    visible_len = visible_width(s)
    if visible_len > cur and cur < max_width:
        # append ellipsis if room
        if cur + 1 <= max_width:
            out.append("…")
    return "".join(out)

# Color codes
COLOR_PRIMARY = "\033[35m"  # Magenta
COLOR_SECONDARY = "\033[36m"  # Cyan
COLOR_IN_PROGRESS = "\033[34m"  # Blue
COLOR_SUCCESS = "\033[32m"  # Green
COLOR_DANGER = "\033[31m"  # Red
COLOR_MUTED = "\033[90m"  # Dark gray
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_BG_PRIMARY = "\033[45m"  # Magenta background
COLOR_WHITE = "\033[37m"


def get_tag_color(tag: str) -> str:
    """Get ANSI color code for tag based on hash."""
    colors = [
        "\033[41m",  # Red background
        "\033[43m",  # Yellow background
        "\033[42m",  # Green background
        "\033[44m",  # Blue background
        "\033[45m",  # Magenta background
        "\033[46m",  # Cyan background
    ]
    hash_val = sum(ord(c) for c in tag)
    return colors[hash_val % len(colors)]


def render_board(model) -> str:
    """Render the Kanban board view."""
    lines = []

    # Header: Title and Statistics
    title = f"{COLOR_BOLD}{COLOR_PRIMARY}📋 Kanban Board{COLOR_RESET}"
    stats = render_stats(model)
    header_width = model.width
    title_len = len("📋 Kanban Board")
    stats_len = len(render_stats_plain(model))
    spacer_width = max(1, header_width - title_len - stats_len)

    lines.append(f"{title}{' ' * spacer_width}{stats}")
    lines.append("")

    # Columns
    columns_lines = render_columns(model)
    lines.extend(columns_lines)

    # Error message if present
    if model.error:
        lines.append("")
        lines.append(f"{COLOR_DANGER}{COLOR_BOLD}Error: {model.error}{COLOR_RESET}")

    # Footer
    lines.append("")
    help_text = "← → / h l: Navigate | a: Add | e: Edit | i: Desc | t: Tags | d: Del | m: Move | ?: Help | q: Quit"
    lines.append(f"{COLOR_MUTED}{help_text}{COLOR_RESET}")

    return "\n".join(lines)


def render_stats(model) -> str:
    """Render statistics bar."""
    parts = []
    for col in model.columns:
        parts.append(f"{col.name}: {len(col.tasks)}")

    stats_text = " | ".join(parts)
    if model.current_time:
        time_str = model.current_time.strftime("%Y-%m-%d %H:%M:%S")
        stats_text = f"{stats_text} | 🕒 {time_str}"

    return f"{COLOR_MUTED}{stats_text}{COLOR_RESET}"


def render_stats_plain(model) -> str:
    """Render statistics bar (plain text without colors)."""
    parts = []
    for col in model.columns:
        parts.append(f"{col.name}: {len(col.tasks)}")

    stats_text = " | ".join(parts)
    if model.current_time:
        time_str = model.current_time.strftime("%Y-%m-%d %H:%M:%S")
        stats_text = f"{stats_text} | 🕒 {time_str}"

    return stats_text


def render_columns(model) -> List[str]:
    """Render all columns side by side."""
    MAX_VISIBLE_TASKS = 10
    lines = []

    # Get column contents (collect inner lines first so we can equalize heights)
    columns_contents = []  # list of (lines, is_active)
    for col_idx, col in enumerate(model.columns):
        col_content = []

        # Column title with status color
        if col.status == TaskStatus.IN_PROGRESS:
            title_color = COLOR_IN_PROGRESS
        elif col.status == TaskStatus.DONE:
            title_color = COLOR_SUCCESS
        else:
            title_color = COLOR_MUTED

        title = f"{COLOR_BOLD}{title_color}{col.name}{COLOR_RESET}"
        col_content.append(title)

        # Scroll up indicator
        offset = model.scroll_offsets[col_idx]
        if offset > 0:
            col_content.append(f"{COLOR_MUTED}  ▲ more above{COLOR_RESET}")

        # Tasks (visible range only)
        if len(col.tasks) == 0:
            col_content.append(f"{COLOR_MUTED}No tasks{COLOR_RESET}")
        else:
            end_idx = min(offset + MAX_VISIBLE_TASKS, len(col.tasks))
            for i in range(offset, end_idx):
                task = col.tasks[i]
                is_active = col_idx == model.current_column and i == model.current_task
                task_view = render_task(task, is_active)
                col_content.append(task_view)

        # Scroll down indicator
        if offset + MAX_VISIBLE_TASKS < len(col.tasks):
            col_content.append(f"{COLOR_MUTED}  ▼ more below{COLOR_RESET}")

        columns_contents.append((col_content, col_idx == model.current_column))

    # Determine max inner lines and render bordered boxes with equal heights
    column_lines = []
    if columns_contents:
        max_inner = max(len(lines) for lines, _ in columns_contents)
        for lines_inner, is_active in columns_contents:
            # pad inner lines to max_inner
            padded_inner = list(lines_inner)
            while len(padded_inner) < max_inner:
                padded_inner.append("")
            bordered = render_column_box("\n".join(padded_inner), is_active)
            column_lines.append(bordered)

    # Join columns horizontally
    if column_lines:
        # Split each column into lines and join horizontally
        col_line_lists = [col.split("\n") for col in column_lines]
        max_lines = max(len(l) for l in col_line_lists)

        # Pad to same height
        for line_list in col_line_lists:
            while len(line_list) < max_lines:
                line_list.append(" " * 30)

        # Join horizontally
        for i in range(max_lines):
            parts = []
            for col_lines in col_line_lists:
                parts.append(col_lines[i] if i < len(col_lines) else " " * 30)
            lines.append("  ".join(parts))

    return lines


def render_column_box(content: str, is_active: bool) -> str:
    """Render column with box border."""
    border_color = COLOR_BOLD if is_active else COLOR_RESET
    lines = content.split("\n")

    # Box drawing
    width = 30
    top = f"{border_color}┌{'─' * (width - 2)}┐{COLOR_RESET}"
    bottom = f"{border_color}└{'─' * (width - 2)}┘{COLOR_RESET}"

    boxed_lines = [top]
    inner_width = width - 2
    for line in lines:
        # Truncate visible content if too long
        vlen = visible_width(line)
        if vlen > inner_width:
            visible_part = truncate_ansi(line, inner_width - 1)
            line_display = visible_part
        else:
            line_display = line

        pad = inner_width - visible_width(line_display)
        if pad < 0:
            pad = 0
        padded_line = line_display + " " * pad
        boxed_lines.append(f"{border_color}│{COLOR_RESET}{padded_line}{border_color}│{COLOR_RESET}")
    boxed_lines.append(bottom)

    return "\n".join(boxed_lines)


def render_task(task: Task, is_active: bool) -> str:
    """Render a single task."""
    # Task title
    text = f"• {task.title}"

    # Add tags if present
    if task.tags:
        text += "\n  "
        for i, tag in enumerate(task.tags):
            if i > 2:
                text += f"+{len(task.tags) - 3}"
                break
            tag_color = get_tag_color(tag)
            text += f"{tag_color}{COLOR_WHITE} {tag} {COLOR_RESET}"
            if i < len(task.tags) - 1 and i < 2:
                text += " "

    if is_active:
        return f"{COLOR_BG_PRIMARY}{COLOR_WHITE}{COLOR_BOLD}{text}{COLOR_RESET}"
    else:
        return text


def render_add_task(model) -> str:
    """Render add task view."""
    lines = [
        f"{COLOR_BOLD}{COLOR_PRIMARY}➕ Add New Task{COLOR_RESET}",
        "",
        f"{COLOR_SECONDARY}Adding to column: {model.columns[model.current_column].name}{COLOR_RESET}",
        "",
        f"Input: {model.text_input}_",
        "",
        f"{COLOR_MUTED}Enter: Save | Esc: Cancel{COLOR_RESET}",
    ]
    return "\n".join(lines)


def render_edit_task(model) -> str:
    """Render edit task view."""
    lines = [
        f"{COLOR_BOLD}{COLOR_PRIMARY}✏️  Edit Task{COLOR_RESET}",
        "",
        f"Input: {model.text_input}_",
        "",
        f"{COLOR_MUTED}Enter: Save | Esc: Cancel{COLOR_RESET}",
    ]
    return "\n".join(lines)


def render_edit_description(model) -> str:
    """Render edit description view."""
    task = model.get_current_task()
    lines = [
        f"{COLOR_BOLD}{COLOR_PRIMARY}📝 Edit Task Description{COLOR_RESET}",
        "",
    ]

    if task:
        lines.append(f"{COLOR_SECONDARY}Task: {task.title}{COLOR_RESET}")
        lines.append("")

    lines.extend([
        f"Input: {model.text_input}",
        "",
        f"{COLOR_MUTED}Ctrl+S: Save | Esc: Cancel{COLOR_RESET}",
    ])
    return "\n".join(lines)


def render_edit_tags(model) -> str:
    """Render edit tags view."""
    task = model.get_current_task()
    lines = [
        f"{COLOR_BOLD}{COLOR_PRIMARY}🏷️  Edit Tags{COLOR_RESET}",
        "",
    ]

    if task:
        lines.append(f"{COLOR_SECONDARY}Task: {task.title}{COLOR_RESET}")
        lines.append("")

    lines.extend([
        f"{COLOR_MUTED}Separate tags with commas (e.g., bug, urgent, feature){COLOR_RESET}",
        "",
        f"Input: {model.text_input}_",
        "",
        f"{COLOR_MUTED}Enter: Save | Esc: Cancel{COLOR_RESET}",
    ])
    return "\n".join(lines)


def render_confirm_delete(model) -> str:
    """Render delete confirmation view."""
    task = model.get_current_task()
    lines = [
        f"{COLOR_BOLD}{COLOR_DANGER}⚠️  Confirm Delete{COLOR_RESET}",
        "",
    ]

    if task:
        lines.append(f"{COLOR_DANGER}{COLOR_BOLD}Are you sure you want to delete this task?{COLOR_RESET}")
        lines.append("")
        lines.append(f"{COLOR_BOLD}\"{task.title}\"{COLOR_RESET}")
        lines.append("")

    lines.append(f"{COLOR_MUTED}y: Yes, delete | n/Esc: Cancel{COLOR_RESET}")
    return "\n".join(lines)


def render_help(model) -> str:
    """Render help view."""
    help_text = f"""{COLOR_BOLD}{COLOR_PRIMARY}❓ Help{COLOR_RESET}

{COLOR_BOLD}Navigation:{COLOR_RESET}
  ← → or h l    Move between columns
  ↑ ↓ or j k    Move between tasks

{COLOR_BOLD}Actions:{COLOR_RESET}
  a             Add new task to current column
  e or Enter    Edit selected task title
  i             Edit selected task description
  t             Edit selected task tags
  d or Delete   Delete selected task
  m             Move task to next column

{COLOR_BOLD}Other:{COLOR_RESET}
  ?             Show this help
  q or Ctrl+C   Quit application
  Esc           Cancel current action or quit

{COLOR_MUTED}Press any key to return to board...{COLOR_RESET}
"""
    return help_text
