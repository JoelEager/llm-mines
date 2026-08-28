#!/usr/bin/env python3
"""
AWS Bedrock CLI runner script for Minesweeper MCP.
Runs a game loop using AWS Bedrock converse API with thinking trace extraction and logging.
"""

import boto3
import common

MODEL_ID = "amazon.nova-pro-v1:0"
# MODEL_ID = "us.meta.llama3-3-70b-instruct-v1:0"
# MODEL_ID = "mistral.ministral-3-14b-instruct"

SYSTEM_PROMPT = "You are an expert Minesweeper solver. Think step-by-step to analyze the board state and logically deduce guaranteed safe cells to reveal or mine cells to flag before taking an action."

PROMPT = """Play a game of Minesweeper using the `minesweeper_action` tool. Your goal is to reveal all non-mine cells without detonating any mines.

### Board Format & Symbols
- Grid coordinates are 0-indexed: `x` is column (0 is left-most), `y` is row (0 is top-most).
- `?`: Unknown / hidden cell.
- `-`: Revealed safe cell (0 adjacent mines).
- `1`-`8`: Revealed safe cell with that number of neighboring mines (in surrounding 8 cells).
- `F`: Flagged cell (marked as a mine).
- `X`: Exploded mine.

### Strategy Rules
1. Start by revealing cell (x=0, y=0).
2. For any numbered cell (`1`-`8`), check its 8 surrounding neighbors:
   - If (hidden + flagged neighbors) equals cell number: all hidden neighbors are mines -> flag them (`flag=True`).
   - If (flagged neighbors) equals cell number: all hidden neighbors are safe -> reveal them (`flag=False`).
3. Always flag known mines before revealing safe cells. If no guaranteed move exists, pick the safest candidate.
4. Continue making logical moves until the game is won or lost."""
WIDTH = 8
HEIGHT = 8
MINES = 10
MAX_TURNS = 100

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

    turns = 0
    while turns < MAX_TURNS:
        turns += 1
        response = bedrock_client.converse(
            modelId=MODEL_ID, 
            messages=messages, 
            system=[{"text": SYSTEM_PROMPT}],
            inferenceConfig={"temperature": 0.0},
            toolConfig={"tools": [MINESWEEPER_TOOL_SPEC]}
        )
        output_message = response["output"]["message"]
        content_blocks = output_message.get("content", [])
        if not content_blocks:
            output_message["content"] = [{"text": "(No output content provided by model)"}]
            content_blocks = output_message["content"]

        messages.append(output_message)
        tool_requests = []
        for block in content_blocks:
            common.log(f"Model Output Block: {block}")
            if "toolUse" in block:
                tool_requests.append(block)

        if not tool_requests:
            common.log("No native toolUse blocks found in model output. Prompting model to use native tool calling.")
            messages.append({
                "role": "user",
                "content": [{
                    "text": "Please invoke the minesweeper_action tool using native tool calls rather than outputting text/JSON."
                }]
            })
            continue

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

        if common.CURRENT_MINEFIELD and common.CURRENT_MINEFIELD.state in (common.GameState.WON, common.GameState.LOST):
            common.log(f"Game finished with status: {common.CURRENT_MINEFIELD.state.name}. Ending run.")
            print(f"Game finished with status: {common.CURRENT_MINEFIELD.state.name}.")
            break



if __name__ == "__main__":
    common.set_log_filename("bedrock")
    main()
