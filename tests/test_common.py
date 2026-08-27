import tempfile
import pytest
from game_logic.game_model import random_minefield, GameState
import common


def test_validate_action_arguments():
    x, y, flag, err = common.validate_action_arguments({"x": 1, "y": 2, "flag": True})
    assert (x, y, flag, err) == (1, 2, True, None)

    x, y, flag, err = common.validate_action_arguments({"x": 0, "y": 0})
    assert (x, y, flag, err) == (0, 0, False, None)

    _, _, _, err = common.validate_action_arguments("invalid")
    assert "JSON object" in err

    _, _, _, err = common.validate_action_arguments({"x": 1})
    assert "required" in err

    _, _, _, err = common.validate_action_arguments({"x": True, "y": 1})
    assert "integers" in err


def test_process_minesweeper_action():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = f"{tmpdir}/test_proc.log"

        # Initialize game
        mf, res = common.process_minesweeper_action(
            None,
            {"x": 0, "y": 0},
            width=5,
            height=5,
            mines=3,
            log_file_path=log_path
        )
        assert mf is not None
        assert "Action performed: reveal cell at (0, 0)" in res["content"][0]["text"]

        # Action on invalid coords returns error but keeps minefield
        mf_after, res_err = common.process_minesweeper_action(
            mf,
            {"x": 99, "y": 99},
            log_file_path=log_path
        )
        assert mf_after == mf
        assert res_err.get("isError") is True
