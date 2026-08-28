# LLM Mines
An experiment to see how large language models perform at playing Minesweeper. The model interacts with the game via the `minesweeper_action` tool to reveal or flag cells. Based on [terminal-mines](https://github.com/JoelEager/terminal-mines) and modified using [Google Jules](https://jules.google.com/).

This project includes two implementations:
- **Local MCP tool**: Exposes the tool via Model Context Protocol over stdio for use in LM Studio.
- **AWS Bedrock harness**: Implements a gameplay loop for AWS Bedrock models.

Active game state is held in memory for the duration of the Python process. If no game is active or a game ends, a new game starts automatically on the next action. Timestamped log files in `logs/` record all actions for the process. Each script is configured separately using constants at the top of the file.

## Usage
### LM Studio
To connect this tool to LM Studio via MCP, add the server configuration to your LM Studio MCP settings (`mcp_config.json`):
```json
{
  "mcpServers": {
    "minesweeper": {
      "command": "python3",
      "args": [
        "/absolute/path/to/mcp-mines/tool.py"
      ]
    }
  }
}
```

In my testing I had the most success with the below prompt. Enable both the minesweeper and JS code sandbox tools.
```text
Play a game of Minesweeper using the `minesweeper_action` tool. Use the JavaScript code tool to assist you in making logical moves.

### Rules & Objective
- The grid contains hidden mines. Your goal is to reveal all non-mine cells without detonating any mines.
- Revealing a mine immediately ends the game in defeat.
- The first move is always safe; if you target a mine on your first turn, it is automatically relocated.

### Output Format & Interpretation
The `minesweeper_action` tool returns a text grid representing the board.
- Grid coordinates are 0-indexed: `x` represents the column (0 is left-most), and `y` represents the row (0 is top-most).
- Each character in the text grid represents a cell:
  - `?`: Unknown / hidden cell.
  - `-`: Revealed safe cell with zero adjacent mines.
  - `1`-`8`: Revealed safe cell with that exact number of neighboring mines (in the 8 surrounding cells).
  - `F`: Flagged cell (marked by you as a mine).
  - `X`: Exploded mine (game over).

### Instructions for the Model
1. **Initial Action**: Start by calling `minesweeper_action(x=0, y=0, flag=False)` (or another corner/center cell) to reveal the initial area.
2. **Code Generation**: Implement JavaScript code to help you select the best next move guided by these strategy hints.
   - For any numbered cell (`1`-`8`), count its 8 surrounding adjacent neighbors (including diagonals).
   - If the number of hidden (`?`) plus flagged (`F`) neighbors equals the cell's number, all remaining hidden neighbors are mines—flag them using `flag=True`.
   - If the number of flagged (`F`) neighbors already equals the cell's number, all remaining hidden (`?`) neighbors are safe—reveal them using `flag=False`.
   - Be sure you have flagged all known mines before looking for safe cells to reveal.
3. **Iterative Play**: Repeat the following steps until the game ends.
   1. Analyze the board and update your JavaScript helper.
   2. Use it to select the best next move.
   3. Use the minesweeper tool to take that action.
```

### Bedrock
Make sure your AWS credentials are set up (e.g. via AWS CLI or environment variables), install boto3, and then run:
```bash
python3 bedrock.py
```

All of the bedrock models I've tried are pretty incompetent and do worse than the above approach.
