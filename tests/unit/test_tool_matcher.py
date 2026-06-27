"""Tests for tool_matcher."""
from datetime import datetime, timezone

from eval_framework.scoring.tool_matcher import ToolMatcher
from eval_framework.models import ToolCall, ToolCallStep

NOW = datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)


class TestToolMatcher:
    def test_exact_sequence_match(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(
                    tool_name="Read", params={"file_path": "/a.py"}
                ),
                result={},
                timestamp=NOW,
                duration_ms=0,
            ),
            ToolCallStep(
                step_index=1,
                tool_call=ToolCall(
                    tool_name="Edit", params={"file_path": "/a.py"}
                ),
                result={},
                timestamp=NOW,
                duration_ms=0,
            ),
        ]
        expected = ["Read", "Edit"]
        score = ToolMatcher.match_sequence(steps, expected)
        assert score == 1.0

    def test_partial_sequence_match(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(tool_name="Read", params={}),
                result={},
                timestamp=NOW,
                duration_ms=0,
            ),
        ]
        expected = ["Read", "Edit", "Write"]
        score = ToolMatcher.match_sequence(steps, expected)
        assert score == 1 / 3

    def test_tool_match_with_key_params(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(
                    tool_name="Bash",
                    params={
                        "command": "pytest tests/",
                        "timeout": 30000,
                    },
                ),
                result={},
                timestamp=NOW,
                duration_ms=0,
            ),
        ]
        expected_tool = "Bash"
        key_params = ["command"]
        score = ToolMatcher.match_tool_params(
            steps, expected_tool, key_params
        )
        assert score == 1.0

    def test_tool_match_missing_param(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(
                    tool_name="Bash",
                    params={"description": "run tests"},
                ),
                result={},
                timestamp=NOW,
                duration_ms=0,
            ),
        ]
        expected_tool = "Bash"
        key_params = ["command"]
        score = ToolMatcher.match_tool_params(
            steps, expected_tool, key_params
        )
        assert score == 0.0
