# Minesweeper MCP Server

An LM Studio-compatible Model Context Protocol (MCP) tool interface over Standard IO (stdio) for playing Minesweeper with LLMs.

## Overview

This project turns Minesweeper into an interactive tool for Large Language Models. Models can interact with the game via the `minesweeper_action` MCP tool to reveal or flag cells on a grid.

### Features
- **MCP Tool Protocol**: Exposes `minesweeper_action(x, y, flag)` over stdio.
- **State Persistence**: Persists active game state in `state.json`. If no game is active, a new game starts automatically.
- **Configurable Difficulty**: Configured via `config.json` next to the code (presets or custom dimensions).
- **Dual Render Engine**:
  - **Concise format**: Compact grid text returned directly to the LLM.
  - **Human-readable format**: Clean ASCII/Unicode box-drawing format saved in logs.
- **Comprehensive Logging**: Individual timestamped game logs in `logs/` and end-of-game summary entries in `logs/master.log`.

---

## Configuration

The game difficulty can be customized in `config.json` located in the root directory.

### Using a Preset Difficulty

```json
{
  "difficulty": "easy"
}
```

Preset difficulties:
- `"easy"`: 8x8 grid with 10 mines
- `"balanced"`: 20x15 grid with 35 mines
- `"intermediate"`: 16x16 grid with 40 mines
- `"challenging"`: 25x20 grid with 70 mines
- `"expert"`: 16x30 grid with 99 mines

### Using a Custom Difficulty

You can also specify a custom grid size and mine count in `config.json` as an object:

```json
{
  "difficulty": {
    "width": 10,
    "height": 10,
    "mines": 15
  }
}
```

---

## LM Studio Setup

To connect this tool to LM Studio via MCP, add the server configuration to your LM Studio MCP settings (`mcp_config.json`):

```json
{
  "mcpServers": {
    "minesweeper": {
      "command": "python3",
      "args": [
        "/absolute/path/to/terminal-mines/tool.py"
      ]
    }
  }
}
```

*(Replace `/absolute/path/to/terminal-mines/tool.py` with the absolute path to `tool.py` on your machine)*

---

## Example Prompt for LLM

Once configured in LM Studio, you can prompt the AI model as follows:

```text
Please play a game of Minesweeper using the `minesweeper_action` tool.
Start by revealing cell (0, 0), then analyze the returned grid board state to decide your next moves logically until the game is won or lost.
```
