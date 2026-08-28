#!/usr/bin/env python3
"""
LM Studio compatible Model Context Protocol (MCP) stdio interface for Minesweeper.
"""

import sys
import json
import traceback
import common

WIDTH = 5
HEIGHT = 5
MINES = 4


def format_mcp_result(result):
    """Format result dict for MCP tool call output."""
    res = {
        "content": [
            {
                "type": "text",
                "text": result["text"]
            }
        ]
    }
    if result.get("is_error"):
        res["isError"] = True
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
            raw_res = common.process_minesweeper_action(arguments, WIDTH, HEIGHT, MINES)
            res = format_mcp_result(raw_res)
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
        line = sys.stdin.readline().strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except Exception:
            common.log(traceback.format_exc())
            continue


if __name__ == "__main__":
    common.set_log_filename("tool")
    main()
