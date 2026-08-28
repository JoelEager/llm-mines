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


def test_process_minesweeper_action(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(common, "LOGS_DIR", tmpdir)
        common.set_log_filename("test")

        res = common.process_minesweeper_action(
            {"x": 0, "y": 0},
            width=5,
            height=5,
            mines=3
        )
        assert res["is_error"] is False
        assert "Action performed: reveal cell at (0, 0)" in res["text"]

        import tool
        import bedrock

        mcp_res = tool.format_mcp_result(res)
        assert mcp_res["content"][0]["text"] == res["text"]
        assert "type" in mcp_res["content"][0]

        bedrock_res = bedrock.format_bedrock_result(res)
        assert bedrock_res["content"][0]["text"] == res["text"]
        assert "type" not in bedrock_res["content"][0]

        # Action on invalid coords returns error
        res_err = common.process_minesweeper_action(
            {"x": 99, "y": 99},
            width=5,
            height=5,
            mines=3
        )
        assert res_err.get("is_error") is True
        mcp_err = tool.format_mcp_result(res_err)
        assert mcp_err.get("isError") is True
        bedrock_err = bedrock.format_bedrock_result(res_err)
        assert bedrock_err.get("status") == "error"
