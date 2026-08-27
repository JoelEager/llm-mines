#!/usr/bin/env python3
"""
LM Studio compatible Model Context Protocol (MCP) stdio interface for Minesweeper.
"""

import sys
import os
import json
import datetime
import traceback
from game_logic.game_model import random_minefield, GameState
from game_logic.renderer import render_concise, render_human, render_status

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

SESSION_FILENAME = "session_{}.log".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
SESSION_LOG_PATH = os.path.join(LOGS_DIR, SESSION_FILENAME)

CURRENT_MINEFIELD = None


def init_session():
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(SESSION_LOG_PATH):
        with open(SESSION_LOG_PATH, "a", encoding="utf-8"):
            pass


init_session()


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception:
            pass
    return {"width": 8, "height": 8, "mines": 10}


def get_difficulty_params(config):
    mines = config.get("mines", 10)
    width = config.get("width", 8)
    height = config.get("height", 8)
    return (mines, width, height)


def log_action(action_str, human_render):
    os.makedirs(LOGS_DIR, exist_ok=True)

    timestamp = datetime.datetime.now().isoformat()
    log_entry = (
        "=== {} ===\n"
        "Action: {}\n"
        "{}\n\n"
    ).format(timestamp, action_str, human_render)

    with open(SESSION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)


def handle_minesweeper_action(arguments):
    global CURRENT_MINEFIELD

    x = arguments.get("x")
    y = arguments.get("y")
    flag = arguments.get("flag", False)

    if x is None or y is None:
        return {"content": [{"type": "text", "text": "Error: Both 'x' and 'y' parameters are required."}], "isError": True}

    if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, int) or not isinstance(y, int):
        return {"content": [{"type": "text", "text": "Error: 'x' and 'y' parameters must be integers."}], "isError": True}

    # Start a new game if no game in progress or if existing game ended
    if CURRENT_MINEFIELD is None or CURRENT_MINEFIELD.state != GameState.IN_PROGRESS:
        config = load_config()
        diff_params = get_difficulty_params(config)
        CURRENT_MINEFIELD = random_minefield(*diff_params)

    # Perform action
    action_type = "flag" if flag else "reveal"
    try:
        if flag:
            CURRENT_MINEFIELD.flag_cell(x, y)
        else:
            CURRENT_MINEFIELD.reveal_cell(x, y)
    except (IndexError, TypeError, ValueError) as e:
        return {"content": [{"type": "text", "text": "Error: {}".format(str(e))}], "isError": True}

    concise = render_concise(CURRENT_MINEFIELD)
    human = render_human(CURRENT_MINEFIELD)
    action_str = "{} cell at ({}, {})".format(action_type, x, y)

    # Log action and state
    log_action(action_str, human)

    # Prepare output
    output_text = "Action performed: {}\nStatus: {}\nBoard:\n{}".format(
        action_str, render_status(CURRENT_MINEFIELD), concise
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
