# MCP Mines
An LM Studio-compatible Model Context Protocol (MCP) tool interface over Standard IO (stdio) for playing Minesweeper with LLMs. Models can interact with the game via the `minesweeper_action` tool to reveal or flag cells. Based on [terminal-mines](https://github.com/JoelEager/terminal-mines) and modified using [Google Jules](https://jules.google.com/).

## Features
- **MCP Tool Protocol**: Exposes `minesweeper_action(x, y, flag)` over stdio.
- **State Persistence**: Persists active game state via `state.json` in the repo root. If no game is active a new game starts automatically. *To abandon a game in progress delete this file.*
- **Configurable Difficulty**: Configured via `config.json` in the repo root.
- **Logging**: Individual timestamped game logs in `logs/` and end-of-game summary entries in `logs/master.log`.

### Using a Preset Difficulty
- `"easy"`: 8x8 grid with 10 mines
- `"balanced"`: 20x15 grid with 35 mines
- `"intermediate"`: 16x16 grid with 40 mines
- `"challenging"`: 25x20 grid with 70 mines
- `"expert"`: 16x30 grid with 99 mines

Example:
```json
{
  "difficulty": "easy"
}
```

### Using a Custom Difficulty
You can also specify a custom grid size and mine count:
```json
{
  "difficulty": {
    "width": 10,
    "height": 10,
    "mines": 15
  }
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
> Play a game of Minesweeper using the `minesweeper_action` tool. Start by revealing cell (0, 0), then analyze the returned grid board state to decide your next moves logically until the game is won or lost.
