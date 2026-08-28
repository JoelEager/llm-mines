import os
import tempfile
import pytest
from game_logic.game_model import Minefield, GameState, random_minefield
from game_logic.renderer import render_human, render_concise
import tool
import common


def test_utf8_logging(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(common, "LOGS_DIR", tmpdir)
        common.set_log_filename("test")
        human = render_human(random_minefield(5, 5, 5))

        # Test writing log entry without raising UnicodeEncodeError in non-UTF-8 environments
        common.log_action("reveal cell at (0, 0)", human)
        assert os.path.exists(common.LOG_FILE)

        with open(common.LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            assert "reveal cell at (0, 0)" in content


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


def test_handle_minesweeper_action_validation(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(common, "LOGS_DIR", tmpdir)
        common.set_log_filename("test")

        res_missing = tool.handle_request({"id": 1, "method": "tools/call", "params": {"name": "minesweeper_action", "arguments": {"x": 0}}})["result"]
        assert res_missing.get("isError") is True

        res_invalid_type = tool.handle_request({"id": 1, "method": "tools/call", "params": {"name": "minesweeper_action", "arguments": {"x": "abc", "y": 0}}})["result"]
        assert res_invalid_type.get("isError") is True

        # True is coerced to integer 1
        res_bool = tool.handle_request({"id": 1, "method": "tools/call", "params": {"name": "minesweeper_action", "arguments": {"x": True, "y": 0}}})["result"]
        assert res_bool.get("isError") is None or res_bool.get("isError") is False

        res_out_of_bounds = tool.handle_request({"id": 1, "method": "tools/call", "params": {"name": "minesweeper_action", "arguments": {"x": 999, "y": 999}}})["result"]
        assert res_out_of_bounds.get("isError") is True
