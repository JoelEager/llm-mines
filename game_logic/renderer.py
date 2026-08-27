"""
Handles the rendering of the game state into concise or human readable formats.
"""

from itertools import chain
from .game_model import GameState, CellState


def render_concise(minefield):
    """
    Renders the game board in a concise format without borders or stats, optimized for LLM consumption.
    """
    lines = []
    for y in range(minefield.height):
        row = [minefield.get_cell(x, y).state.value for x in range(minefield.width)]
        lines.append(" ".join(row))
    return "\n".join(lines)


def render_human(minefield):
    """
    Renders the game state using unicode box-drawing characters without ANSI colors.
    """
    def gen_lines():
        yield chr(0x250C) + chr(0x2500) * (minefield.width * 2 + 1) + chr(0x2510)

        for iter_y in range(minefield.height):
            iter_cells = (minefield.get_cell(iter_x, iter_y).state.value for iter_x in range(minefield.width))
            yield " ".join(chain(chr(0x2502), iter_cells, chr(0x2502)))

        yield chr(0x2514) + chr(0x2500) * (minefield.width * 2 + 1) + chr(0x2518)

        if minefield.state == GameState.WON:
            yield " Game won"
        elif minefield.state == GameState.LOST:
            yield " Game lost"
        else:
            remain_safe = len([cell for cell in minefield.cells if not cell.is_mine and cell.state in (CellState.UNKNOWN, CellState.FLAGGED)])
            yield " {} / {} marked; {} safe {}".format(
                len([cell for cell in minefield.cells if cell.state == CellState.FLAGGED]),
                minefield.num_mines,
                remain_safe,
                "cell remains" if remain_safe == 1 else "cells remain"
            )

    return "\n".join(gen_lines())


def render(minefield, human=False):
    """
    Renders the minefield. If human is True, returns human readable box format. Otherwise returns concise format.
    """
    if human:
        return render_human(minefield)
    return render_concise(minefield)
