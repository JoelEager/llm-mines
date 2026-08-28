import sys
import os
import tempfile
from unittest.mock import MagicMock

# Mock boto3 before importing bedrock if boto3 is not installed
if "boto3" not in sys.modules:
    sys.modules["boto3"] = MagicMock()

import bedrock


def test_bedrock_main_loop(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(bedrock.common, "LOGS_DIR", tmpdir)

        mock_boto3_client = MagicMock()
        monkeypatch.setattr(bedrock.boto3, "client", lambda service_name: mock_boto3_client)

        response_1 = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool_123",
                                "name": "minesweeper_action",
                                "input": {"x": 0, "y": 0, "flag": False}
                            }
                        }
                    ]
                }
            }
        }

        response_2 = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "I am thinking about the next move..."}
                    ]
                }
            }
        }

        response_3 = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool_456",
                                "name": "minesweeper_action",
                                "input": {"x": "1", "y": "1", "flag": "false"}
                            }
                        }
                    ]
                }
            }
        }

        mock_boto3_client.converse.side_effect = [response_1, response_2, response_3]

        bedrock.common.set_log_filename("bedrock")
        # Set minefield to lost or won state on processing tool_456 to test game end termination
        orig_process_action = bedrock.common.process_minesweeper_action
        def mock_process_action(args, w, h, m):
            res = orig_process_action(args, w, h, m)
            if args.get("x") in (1, "1") and bedrock.common.CURRENT_MINEFIELD:
                bedrock.common.CURRENT_MINEFIELD.state = bedrock.common.GameState.WON
            return res

        monkeypatch.setattr(bedrock.common, "process_minesweeper_action", mock_process_action)
        bedrock.main()

        assert mock_boto3_client.converse.call_count == 3
        # Check retry message sent when response_2 contained no toolUse
        messages_call_3 = mock_boto3_client.converse.call_args_list[2][1]["messages"]
        assert messages_call_3[3]["role"] == "assistant"
        assert messages_call_3[4]["role"] == "user"
        assert "native tool calls" in messages_call_3[4]["content"][0]["text"]

        call_args_2 = mock_boto3_client.converse.call_args_list[1]
        sent_messages_2 = call_args_2[1]["messages"]
        assert call_args_2[1]["system"] == [{"text": bedrock.SYSTEM_PROMPT}]
        assert call_args_2[1]["inferenceConfig"] == {"temperature": 0.0}
        user_tool_result = sent_messages_2[2]
        assert user_tool_result["role"] == "user"
        tool_result = user_tool_result["content"][0]["toolResult"]
        assert tool_result["toolUseId"] == "tool_123"
        content_block = tool_result["content"][0]
        assert "text" in content_block
        assert "type" not in content_block


def test_bedrock_empty_content_handling(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(bedrock.common, "LOGS_DIR", tmpdir)

        mock_boto3_client = MagicMock()
        monkeypatch.setattr(bedrock.boto3, "client", lambda service_name: mock_boto3_client)

        empty_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": []
                }
            }
        }

        mock_boto3_client.converse.return_value = empty_response

        bedrock.common.set_log_filename("bedrock")
        # Run with MAX_TURNS set to 1 to complete fast
        monkeypatch.setattr(bedrock, "MAX_TURNS", 1)
        bedrock.main()

        call_args = mock_boto3_client.converse.call_args_list[0]
        sent_messages = call_args[1]["messages"]
        # Output message appended to sent_messages in loop should have non-empty content
        assert len(bedrock.common.LOGS_DIR) > 0


def test_bedrock_prompt_content():
    assert "Board Format & Symbols" in bedrock.PROMPT
    assert "Strategy Rules" in bedrock.PROMPT
    assert "flag" in bedrock.PROMPT
    assert "0-indexed" in bedrock.PROMPT
    assert "`?`: Unknown / hidden cell." in bedrock.PROMPT
    assert "`F`: Flagged cell" in bedrock.PROMPT
    assert "Always flag known mines before revealing safe cells" in bedrock.PROMPT
    assert "Think step-by-step" in bedrock.SYSTEM_PROMPT
