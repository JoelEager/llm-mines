#!/usr/bin/env python3
"""
LM Studio compatible Model Context Protocol (MCP) stdio interface for Minesweeper.
"""

import sys
import json
import os
import traceback
import common

WIDTH = common.DEFAULT_WIDTH
HEIGHT = common.DEFAULT_HEIGHT
MINES = common.DEFAULT_MINES

SESSION_FILENAME = common.get_log_filename(prefix="tool", timestamp_format="%Y-%m-%d_%H-%M")
SESSION_LOG_PATH = os.path.join(common.LOGS_DIR, SESSION_FILENAME)

CURRENT_MINEFIELD = None


def init_session():
    common.ensure_logs_dir()
    if not os.path.exists(SESSION_LOG_PATH):
        with open(SESSION_LOG_PATH, "a", encoding="utf-8"):
            pass


init_session()


def log_action(action_str, human_render):
    common.log_action(SESSION_LOG_PATH, action_str, human_render)


def handle_minesweeper_action(arguments):
    global CURRENT_MINEFIELD
    CURRENT_MINEFIELD, res = common.process_minesweeper_action(
        CURRENT_MINEFIELD,
        arguments,
        width=WIDTH,
        height=HEIGHT,
        mines=MINES,
        log_file_path=SESSION_LOG_PATH
    )
    return res


def handle_request(request):
    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if method == "initialize":
        return {
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
                    "message": f"Tool not found: {tool_name}"
                }
            }

    else:
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
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
