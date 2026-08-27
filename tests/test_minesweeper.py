import os
import tempfile
import pytest
from game_logic import Minefield, GameState, CellState, random_minefield, render_human, render_concise
import tool


def test_utf8_logging(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(tool, "LOGS_DIR", tmpdir)
        concise = render_concise(random_minefield(5, 5, 5))
        human = render_human(random_minefield(5, 5, 5))

        # Test writing log entry without raising UnicodeEncodeError in non-UTF-8 environments
        tool.log_action("test_game", "reveal cell at (0, 0)", human, "IN_PROGRESS")
        game_log = os.path.join(tmpdir, "test_game.log")
        assert os.path.exists(game_log)

        with open(game_log, "r", encoding="utf-8") as f:
            content = f.read()
            assert "reveal cell at (0, 0)" in content

        # Test master log on game over
        tool.log_action("test_game", "reveal cell at (0, 0)", human, "WON")
        master_log = os.path.join(tmpdir, "master.log")
        assert os.path.exists(master_log)


def test_misflagged_cell_does_not_trigger_false_win():
    m = Minefield(2, 2, {"1,1"})
    # Flag cell (0, 0) which is safe!
    m.flag_cell(0, 0)
    # Reveal other non-mine cells (0, 1) and (1, 0)
    m.reveal_cell(0, 1)
    m.reveal_cell(1, 0)

    # Game should still be IN_PROGRESS because (0, 0) is safe and not revealed
    assert m.state == GameState.IN_PROGRESS

    # Check human renderer safe cell count includes flagged safe cell
    human_text = render_human(m)
    assert "1 safe cell remains" in human_text or "1 safe cells remain" in human_text

    # Unflag (0, 0) and reveal it
    m.flag_cell(0, 0)
    m.reveal_cell(0, 0)
    assert m.state == GameState.WON


def test_random_minefield_bounds():
    m = random_minefield(100, 3, 3)
    assert m.num_mines == 8

    with pytest.raises(ValueError):
        random_minefield(5, 0, 5)


def test_handle_minesweeper_action_validation():
    res_missing = tool.handle_minesweeper_action({"x": 0})
    assert res_missing.get("isError") is True

    res_invalid_type = tool.handle_minesweeper_action({"x": "abc", "y": 0})
    assert res_invalid_type.get("isError") is True

    res_bool = tool.handle_minesweeper_action({"x": True, "y": 0})
    assert res_bool.get("isError") is True

    res_out_of_bounds = tool.handle_minesweeper_action({"x": 999, "y": 999})
    assert res_out_of_bounds.get("isError") is True
