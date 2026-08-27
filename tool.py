#!/usr/bin/env python3
"""
LM Studio compatible Model Context Protocol (MCP) stdio interface for Minesweeper.
"""

import sys
import os
import json
import datetime
import traceback
from game_logic import Minefield, random_minefield, GameState, render_concise, render_human

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "state.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

DIFFICULTY_PRESETS = {
    "balanced": (35, 20, 15),
    "challenging": (70, 25, 20),
    "easy": (10, 8, 8),
    "intermediate": (40, 16, 16),
    "expert": (99, 16, 30)
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception:
            pass
    return {"difficulty": "easy"}


def get_difficulty_params(config):
    diff = config.get("difficulty", "easy")
    if isinstance(diff, str) and diff in DIFFICULTY_PRESETS:
        return DIFFICULTY_PRESETS[diff]
    elif isinstance(diff, dict):
        mines = diff.get("mines", 10)
        width = diff.get("width", 8)
        height = diff.get("height", 8)
        return (mines, width, height)
    elif isinstance(diff, (list, tuple)) and len(diff) == 3:
        return tuple(diff)
    return DIFFICULTY_PRESETS["easy"]


def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                minefield = Minefield.from_dict(data["minefield"])
                game_id = data.get("game_id")
                return minefield, game_id
        except Exception:
            pass
    return None, None


def save_state(minefield, game_id):
    data = {
        "game_id": game_id,
        "minefield": minefield.to_dict()
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def remove_state():
    if os.path.exists(STATE_PATH):
        try:
            os.remove(STATE_PATH)
        except OSError:
            pass


def log_action(game_id, action_str, human_render, state_name):
    os.makedirs(LOGS_DIR, exist_ok=True)
    game_log_path = os.path.join(LOGS_DIR, "{}.log".format(game_id))

    timestamp = datetime.datetime.now().isoformat()
    log_entry = (
        "=== Action at {} ===\n"
        "Action: {}\n"
        "State: {}\n"
        "{}\n\n"
    ).format(timestamp, action_str, state_name, human_render)

    with open(game_log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)

    if state_name in ("WON", "LOST"):
        master_log_path = os.path.join(LOGS_DIR, "master.log")
        master_entry = (
            "=== Game {} ===\n"
            "{}\n\n"
        ).format(game_id, human_render)
        with open(master_log_path, "a", encoding="utf-8") as f:
            f.write(master_entry)


def handle_minesweeper_action(arguments):
    x = arguments.get("x")
    y = arguments.get("y")
    flag = arguments.get("flag", False)

    if x is None or y is None:
        return {"content": [{"type": "text", "text": "Error: Both 'x' and 'y' parameters are required."}], "isError": True}

    if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, int) or not isinstance(y, int):
        return {"content": [{"type": "text", "text": "Error: 'x' and 'y' parameters must be integers."}], "isError": True}

    minefield, game_id = load_state()

    # Start a new game if no game in progress or if existing game ended
    if minefield is None or minefield.state != GameState.IN_PROGRESS:
        config = load_config()
        diff_params = get_difficulty_params(config)
        minefield = random_minefield(*diff_params)
        game_id = datetime.datetime.now().strftime("game_%Y-%m-%d_%H-%M")

    # Perform action
    action_type = "flag" if flag else "reveal"
    try:
        if flag:
            minefield.flag_cell(x, y)
        else:
            minefield.reveal_cell(x, y)
    except (IndexError, TypeError, ValueError) as e:
        return {"content": [{"type": "text", "text": "Error: {}".format(str(e))}], "isError": True}

    concise = render_concise(minefield)
    human = render_human(minefield)
    action_str = "{} cell at ({}, {})".format(action_type, x, y)

    # Log action and state
    log_action(game_id, action_str, human, minefield.state.name)

    # Save state or remove if finished
    if minefield.state == GameState.IN_PROGRESS:
        save_state(minefield, game_id)
    else:
        remove_state()

    output_text = "Action performed: {}\nGame State: {}\nBoard:\n{}".format(
        action_str, minefield.state.name, concise
    )
    return {
        "content": [
            {
                "type": "text",
                "text": output_text
            }
        ]
    }


def handle_request(request):
    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if method == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "minesweeper-mcp",
                    "version": "1.0.0"
                }
            }
        }
        return response

    elif method == "notifications/initialized":
        return None

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "minesweeper_action",
                        "description": "Make a move in Minesweeper by revealing or flagging a cell at (x, y).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "integer",
                                    "description": "The X coordinate (0-indexed from left)."
                                },
                                "y": {
                                    "type": "integer",
                                    "description": "The Y coordinate (0-indexed from top)."
                                },
                                "flag": {
                                    "type": "boolean",
                                    "description": "True to flag/unflag the cell, False to reveal it. Defaults to False."
                                }
                            },
                            "required": ["x", "y"]
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name == "minesweeper_action":
            res = handle_minesweeper_action(arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": res
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": "Tool not found: {}".format(tool_name)
                }
            }

    else:
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found: {}".format(method)
                }
            }
        return None


def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except Exception:
            sys.stderr.write(traceback.format_exc())
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
