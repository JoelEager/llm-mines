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
                        {"text": "Revealed cell (0, 0). Ending run."}
                    ]
                }
            }
        }

        mock_boto3_client.converse.side_effect = [response_1, response_2]

        bedrock.common.set_log_filename("bedrock")
        bedrock.main()

        # Verify second call to converse included tool result formatted without 'type' key
        assert mock_boto3_client.converse.call_count == 2
        call_args = mock_boto3_client.converse.call_args_list[1]
        sent_messages = call_args[1]["messages"]
        assert call_args[1]["system"] == [{"text": bedrock.SYSTEM_PROMPT}]
        assert call_args[1]["inferenceConfig"] == {"temperature": 0.0}
        user_tool_result = sent_messages[2]
        assert user_tool_result["role"] == "user"
        tool_result = user_tool_result["content"][0]["toolResult"]
        assert tool_result["toolUseId"] == "tool_123"
        content_block = tool_result["content"][0]
        assert "text" in content_block
        assert "type" not in content_block


def test_bedrock_prompt_content():
    assert "Board Format & Symbols" in bedrock.PROMPT
    assert "Strategy Rules" in bedrock.PROMPT
    assert "flag" in bedrock.PROMPT
    assert "0-indexed" in bedrock.PROMPT
    assert "`?`: Unknown / hidden cell." in bedrock.PROMPT
    assert "`F`: Flagged cell" in bedrock.PROMPT
    assert "Always flag known mines before revealing safe cells" in bedrock.PROMPT
    assert "Think step-by-step" in bedrock.SYSTEM_PROMPT
