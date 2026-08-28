#!/usr/bin/env python3
"""
AWS Bedrock CLI runner script for Minesweeper MCP.
Runs a game loop using AWS Bedrock converse API with thinking trace extraction and logging.
"""

import boto3
import common

MODEL_ID = "amazon.nova-pro-v1:0"
PROMPT = """Play a game of Minesweeper using the `minesweeper_action` tool.

Input Format:
- Call `minesweeper_action(x, y, flag)` where `x` is column (0-indexed from left), `y` is row (0-indexed from top), and `flag` is boolean (False to reveal, True to flag/unflag).

Output Format:
The tool returns a grid of characters:
- `?`: Hidden cell.
- `-`: Revealed safe cell (0 adjacent mines).
- `1`-`8`: Revealed safe cell with that number of neighboring mines.
- `F`: Flagged cell.
- `X`: Exploded mine.

Instructions:
1. Start by revealing cell (0, 0).
2. Analyze the grid board state after each action.
3. Flag any location you determine to be a mine using `flag=True`.
4. Continue making logical moves until the game is won or lost."""
WIDTH = 8
HEIGHT = 8
MINES = 10

MINESWEEPER_TOOL_SPEC = {
    "toolSpec": {
        "name": "minesweeper_action",
        "description": "Make a move in Minesweeper by revealing or flagging a cell at (x, y).",
        "inputSchema": {
            "json": {
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
    }
}


def format_bedrock_result(result):
    """Format result dict for AWS Bedrock converse toolResult content."""
    res = {
        "content": [
            {
                "text": result["text"]
            }
        ]
    }
    if result.get("is_error"):
        res["status"] = "error"
    return res


def main():
    bedrock_client = boto3.client("bedrock-runtime")
    messages = [
        {
            "role": "user",
            "content": [{"text": PROMPT}]
        }
    ]

    print(f"Logging to {common.LOG_FILE}")
    print("Running via AWS Bedrock...")
    common.log (f"Model name: {MODEL_ID}")
    common.log(f"Prompt: {PROMPT}\n")

    while True:
        response = bedrock_client.converse(
            modelId=MODEL_ID, 
            messages=messages, 
            toolConfig={"tools": [MINESWEEPER_TOOL_SPEC]}
        )
        output_message = response["output"]["message"]
        messages.append(output_message)

        content_blocks = output_message.get("content", [])
        tool_requests = []
        for block in content_blocks:
            common.log(f"Model Output Block: {block}")
            if "toolUse" in block:
                tool_requests.append(block)

        if not tool_requests:
            print("No tool requests found in model output. Ending run.")
            break

        tool_result_contents = []
        for tr in tool_requests:
            tool_use = tr["toolUse"]
            tool_use_id = tool_use["toolUseId"]
            name = tool_use["name"]
            arguments = tool_use.get("input", {})

            common.log(f"Tool Call: {name}({arguments})")
            if name == "minesweeper_action":
                raw_res = common.process_minesweeper_action(arguments, WIDTH, HEIGHT, MINES)
                formatted_res = format_bedrock_result(raw_res)
                tool_result_entry = {
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": formatted_res["content"]
                    }
                }
                if "status" in formatted_res:
                    tool_result_entry["toolResult"]["status"] = formatted_res["status"]
                tool_result_contents.append(tool_result_entry)
            else:
                tool_result_contents.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": f"Error: Unknown tool {name}"}],
                        "status": "error"
                    }
                })

        messages.append({
            "role": "user",
            "content": tool_result_contents
        })



if __name__ == "__main__":
    common.set_log_filename("bedrock")
    main()
