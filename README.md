# MCP Mines
An LM Studio-compatible Model Context Protocol (MCP) tool interface over Standard IO (stdio) for playing Minesweeper with LLMs. Models can interact with the game via the `minesweeper_action` tool to reveal or flag cells. Based on [terminal-mines](https://github.com/JoelEager/terminal-mines) and modified using [Google Jules](https://jules.google.com/).

## Features
- **MCP Tool Protocol**: Exposes `minesweeper_action(x, y, flag)` over stdio.
- **In-Memory State**: Active game state is held in memory for the duration of the server process. If no game is active or a game ends, a new game starts automatically on the next action.
- **Configurable Grid & Mine Count**: Configured via `config.json` in the repo root.
- **Session Logging**: Creates a timestamped session log file in `logs/` whenever the server process starts up, recording all actions for that session. Master entries for completed games are recorded in `logs/master.log`.

### Configuration
You can specify grid size and mine count in `config.json`:
```json
{
  "width": 8,
  "height": 8,
  "mines": 10
}
```

## LM Studio Setup
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

## Example Prompt for LLM
Once configured in LM Studio, you can prompt the AI model as follows:

```text
Play a game of Minesweeper using the `minesweeper_action` tool.

### Rules & Objective
- The grid contains hidden mines. Your goal is to reveal all non-mine cells without detonating any mines.
- Revealing a mine immediately ends the game in defeat (`LOST`).
- The first move is always safe; if you target a mine on your first turn, it is automatically relocated.

### Output Format & Interpretation
The `minesweeper_action` tool returns the current `Game State` (`IN_PROGRESS`, `WON`, or `LOST`) and a text grid representing the board.
- Grid coordinates are 0-indexed: `x` represents the column (0 is left-most), and `y` represents the row (0 is top-most).
- Each character in the text grid represents a cell:
  - `?`: Unknown / hidden cell.
  - `-`: Revealed safe cell with zero adjacent mines.
  - `1`-`8`: Revealed safe cell with that exact number of neighboring mines (in the 8 surrounding cells).
  - `F`: Flagged cell (marked by you as a mine).
  - `X`: Exploded mine (game over).

### Instructions for the Model
1. **Initial Action**: Start by calling `minesweeper_action(x=0, y=0, flag=False)` (or another corner/center cell) to reveal the initial area.
2. **Board Analysis & Deduction**:
   - Inspect the returned text grid. Map the characters to 0-indexed `(x, y)` coordinates where `x` is column index and `y` is row index.
   - For any numbered cell (`1`-`8`), count its 8 surrounding adjacent neighbors (including diagonals).
   - If the number of hidden (`?`) plus flagged (`F`) neighbors equals the cell's number, all remaining hidden neighbors are mines—flag them using `flag=True`.
   - If the number of flagged (`F`) neighbors already equals the cell's number, all remaining hidden (`?`) neighbors are safe—reveal them using `flag=False`.
3. **Iterative Play**: Continue analyzing the board state after every action. Make one or multiple safe logical moves per turn until the game state becomes `WON` or `LOST`. Avoid guessing unless no logical move is possible.
```
