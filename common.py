#!/usr/bin/env python3
"""
Common utilities, constants, and logging logic for Minesweeper MCP tools and bedrock runner.
"""

import os
import datetime
from game_logic.game_model import random_minefield, GameState
from game_logic.renderer import render_concise, render_human, render_status

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

DEFAULT_WIDTH = 8
DEFAULT_HEIGHT = 8
DEFAULT_MINES = 10


def ensure_logs_dir():
    """Ensure the logs directory exists."""
    os.makedirs(LOGS_DIR, exist_ok=True)


def get_log_filename(prefix="tool", timestamp_format="%Y-%m-%d_%H-%M"):
    """Generate a log filename given a prefix and timestamp format."""
    now_str = datetime.datetime.now().strftime(timestamp_format)
    return f"{prefix}_{now_str}.log"


def log_action(log_file_path, action_str, human_render):
    """Log an action and human board render to the specified log file."""
    ensure_logs_dir()
    timestamp = datetime.datetime.now().isoformat()
    log_entry = (
        f"=== {timestamp} ===\n"
        f"Action: {action_str}\n"
        f"{human_render}\n\n"
    )
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_entry)


def validate_action_arguments(arguments):
    """
    Validate action arguments dictionary.
    Returns (x, y, flag, error_message).
    """
    if not isinstance(arguments, dict):
        return None, None, False, "Error: Arguments must be a JSON object."

    x = arguments.get("x")
    y = arguments.get("y")
    flag = arguments.get("flag", False)

    if x is None or y is None:
        return None, None, False, "Error: Both 'x' and 'y' parameters are required."

    if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, int) or not isinstance(y, int):
        return None, None, False, "Error: 'x' and 'y' parameters must be integers."

    return x, y, bool(flag), None


def process_minesweeper_action(minefield, arguments, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, mines=DEFAULT_MINES, log_file_path=None):
    """
    Process a minesweeper action on the given minefield (creating a new one if None or finished).
    Returns (updated_minefield, response_dict).
    """
    x, y, flag, err = validate_action_arguments(arguments)
    if err:
        return minefield, {"content": [{"type": "text", "text": err}], "isError": True}

    if minefield is None or minefield.state != GameState.IN_PROGRESS:
        minefield = random_minefield(mines, width, height)

    action_type = "flag" if flag else "reveal"
    try:
        if flag:
            minefield.flag_cell(x, y)
        else:
            minefield.reveal_cell(x, y)
    except (IndexError, TypeError, ValueError) as e:
        return minefield, {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}

    concise = render_concise(minefield)
    human = render_human(minefield)
    action_str = f"{action_type} cell at ({x}, {y})"

    if log_file_path:
        log_action(log_file_path, action_str, human)

    output_text = f"Action performed: {action_str}\nStatus: {render_status(minefield)}\nBoard:\n{concise}"
    return minefield, {
        "content": [
            {
                "type": "text",
                "text": output_text
            }
        ]
    }
