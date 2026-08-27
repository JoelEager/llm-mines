#!/usr/bin/env python3
"""
AWS Bedrock CLI runner script for Minesweeper MCP.
Runs a game loop using AWS Bedrock converse API with thinking trace extraction and logging.
"""

import os
import datetime
import common

MODEL_ID = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
PROMPT = (
    "Play a game of Minesweeper using the minesweeper_action tool. "
    "Start by revealing cell (0, 0), then analyze the returned grid board state "
    "to decide your next moves logically until the game is won or lost."
)
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

CURRENT_MINEFIELD = None


def extract_thinking_trace(message_content):
    """
    Extract thinking/reasoning trace from Bedrock converse message content blocks or text.
    """
    thinking_traces = []
    if not isinstance(message_content, list):
        return ""

    for block in message_content:
        if not isinstance(block, dict):
            continue
        # Bedrock reasoningContent block (Anthropic reasoning / Nova reasoning)
        if "reasoningContent" in block:
            reasoning = block["reasoningContent"]
            if isinstance(reasoning, dict):
                reasoning_text = reasoning.get("reasoningText", {})
                if isinstance(reasoning_text, dict) and "text" in reasoning_text:
                    thinking_traces.append(reasoning_text["text"])
                elif "text" in reasoning:
                    thinking_traces.append(reasoning["text"])
            elif isinstance(reasoning, str):
                thinking_traces.append(reasoning)
        # Check text block for thinking tags <thinking>...</thinking> or <thought>...</thought>
        elif "text" in block:
            text = block["text"]
            if "<thinking>" in text and "</thinking>" in text:
                start = text.find("<thinking>") + len("<thinking>")
                end = text.find("</thinking>")
                thinking_traces.append(text[start:end].strip())
            elif "<thought>" in text and "</thought>" in text:
                start = text.find("<thought>") + len("<thought>")
                end = text.find("</thought>")
                thinking_traces.append(text[start:end].strip())

    return "\n---\n".join(thinking_traces)


def log_run(log_file_path, timestamp, model_id, prompt, thinking_traces):
    common.ensure_logs_dir()
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(f"=== Bedrock Run at {timestamp} ===\n")
        f.write(f"Model Name: {model_id}\n")
        f.write(f"Initial Prompt: {prompt}\n")
        f.write(f"Thinking Traces:\n{thinking_traces if thinking_traces else 'None recorded'}\n")
        f.write("=" * 40 + "\n\n")


def run_bedrock(model_id=MODEL_ID, prompt=PROMPT, bedrock_client=None):
    global CURRENT_MINEFIELD

    if bedrock_client is None:
        import boto3
        bedrock_client = boto3.client("bedrock-runtime")

    timestamp = datetime.datetime.now().isoformat()
    log_filename = common.get_log_filename(prefix="bedrock", timestamp_format="%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(common.LOGS_DIR, log_filename)

    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]

    all_thinking_traces = []

    print(f"\nStarting game run with model: {model_id}")
    print(f"Prompt: {prompt}\n")

    while True:
        converse_kwargs = {
            "modelId": model_id,
            "messages": messages,
            "toolConfig": {"tools": [MINESWEEPER_TOOL_SPEC]}
        }

        response = bedrock_client.converse(**converse_kwargs)

        output_message = response["output"]["message"]
        messages.append(output_message)

        content_blocks = output_message.get("content", [])
        thinking = extract_thinking_trace(content_blocks)
        if thinking:
            all_thinking_traces.append(thinking)
            print(f"[Thinking Trace]:\n{thinking}\n")

        tool_requests = [b for b in content_blocks if "toolUse" in b]
        text_blocks = [b.get("text") for b in content_blocks if "text" in b]

        for tb in text_blocks:
            if tb:
                print(f"Model: {tb}")

        if not tool_requests:
            break

        tool_result_contents = []
        for tr in tool_requests:
            tool_use = tr["toolUse"]
            tool_use_id = tool_use["toolUseId"]
            name = tool_use["name"]
            arguments = tool_use.get("input", {})

            print(f"Tool Call: {name}({arguments})")
            if name == "minesweeper_action":
                CURRENT_MINEFIELD, res = common.process_minesweeper_action(
                    CURRENT_MINEFIELD,
                    arguments,
                    width=WIDTH,
                    height=HEIGHT,
                    mines=MINES,
                    log_file_path=log_file_path
                )
                tool_result_contents.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": res["content"]
                    }
                })
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

    combined_thinking = "\n---\n".join(all_thinking_traces)
    log_run(log_file_path, timestamp, model_id, prompt, combined_thinking)
    print(f"\nRun completed! Saved log to {log_file_path}")
    return log_file_path


def main():
    run_bedrock()


if __name__ == "__main__":
    main()
