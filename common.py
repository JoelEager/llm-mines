"""
Common utilities, constants, and logging logic for Minesweeper MCP tools and bedrock runner.
"""

from os import path, makedirs
from datetime import datetime
from game_logic.game_model import random_minefield, GameState
from game_logic.renderer import render_concise, render_human, render_status

BASE_DIR = path.dirname(path.abspath(__file__))
LOGS_DIR = path.join(BASE_DIR, "logs")

CURRENT_MINEFIELD = None
LOG_FILE = None


def set_log_filename(prefix):
    """Generate a log filename given a prefix."""
    makedirs(LOGS_DIR, exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    global LOG_FILE
    LOG_FILE = path.join(LOGS_DIR, f"{prefix}_{now_str}.log")


def log(message):
    """Log a message to the specified log file."""
    if LOG_FILE is None:
        raise ValueError("LOG_FILE is not set. Call set_log_filename() first.")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def log_action(action_str, human_render):
    """Log an action and human board render to the specified log file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = (
        f"=== {timestamp} ===\n"
        f"Action: {action_str}\n"
        f"{human_render}\n"
    )
    log(log_entry)


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


def process_minesweeper_action(arguments, width, height, mines):
    """
    Process a minesweeper action on the given minefield (creating a new one if None or finished).
    Returns result dict with 'text' and 'is_error'.
    """
    x, y, flag, err = validate_action_arguments(arguments)
    if err:
        return {"text": err, "is_error": True}

    global CURRENT_MINEFIELD
    if CURRENT_MINEFIELD is None or CURRENT_MINEFIELD.state != GameState.IN_PROGRESS:
        CURRENT_MINEFIELD = random_minefield(mines, width, height)

    action_type = "flag" if flag else "reveal"
    try:
        if flag:
            CURRENT_MINEFIELD.flag_cell(x, y)
        else:
            CURRENT_MINEFIELD.reveal_cell(x, y)
    except (IndexError, TypeError, ValueError) as e:
        log(f"Error processing action {action_type} at ({x}, {y}): {e}")
        return {"text": f"Error: {e}", "is_error": True}

    action_str = f"{action_type} cell at ({x}, {y})"
    human = render_human(CURRENT_MINEFIELD)
    log_action(action_str, human)

    concise = render_concise(CURRENT_MINEFIELD)
    output_text = f"Action performed: {action_str}\nStatus: {render_status(CURRENT_MINEFIELD)}\nBoard:\n{concise}"
    return {
        "text": output_text,
        "is_error": False
    }
