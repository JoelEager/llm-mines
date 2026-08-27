import os
import tempfile
from unittest.mock import MagicMock
import bedrock_demo


def test_extract_thinking_trace():
    blocks = [
        {"reasoningContent": {"reasoningText": {"text": "Reasoning block 1"}}},
        {"text": "Normal response text"},
        {"text": "<thinking>Tag thinking trace</thinking>"}
    ]

    extracted = bedrock_demo.extract_thinking_trace(blocks)
    assert "Reasoning block 1" in extracted
    assert "Tag thinking trace" in extracted


def test_run_bedrock_demo_loop(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(bedrock_demo, "LOGS_DIR", tmpdir)

        # Mock bedrock client responses
        mock_client = MagicMock()

        # 1st call: returns tool use request
        response_1 = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"reasoningContent": {"reasoningText": {"text": "Analyzing grid..."}}},
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

        # 2nd call: returns final text response
        response_2 = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "Revealed cell (0, 0). Next move..."}
                    ]
                }
            }
        }

        mock_client.converse.side_effect = [response_1, response_2]

        log_path = bedrock_demo.run_bedrock_demo(
            model_id="custom-bedrock-model",
            prompt="Test prompt",
            bedrock_client=mock_client
        )

        assert os.path.exists(log_path)
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            assert "Model Name: custom-bedrock-model" in log_content
            assert "Initial Prompt: Test prompt" in log_content
            assert "Analyzing grid..." in log_content
