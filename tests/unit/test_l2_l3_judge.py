"""Tests for LLM-as-Judge scoring."""
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from eval_framework.models import (
    AgentTrace,
    Dimension,
    Layer,
    ScoringType,
    TestItem,
    SandboxConfig,
    ScoringConfig,
)
from eval_framework.scoring.l2_l3_judge import L2L3Judge

SAMPLE_JUDGE_RESPONSE = {
    "scores": [
        {"dimension": "D1", "score": 4, "reasoning": "Good code quality."},
        {"dimension": "D2", "score": 3, "reasoning": "Adequate decomposition."},
        {"dimension": "D3", "score": 5, "reasoning": "Excellent tool use."},
        {"dimension": "D4", "score": 2, "reasoning": "No sub-agent usage."},
        {"dimension": "D5", "score": 3, "reasoning": "Basic debugging."},
        {"dimension": "D6", "score": 1, "reasoning": "No memory demonstrated."},
    ]
}


class TestL2L3Judge:
    def test_build_prompt(self):
        """Judge should build a prompt with scenario and trace info."""
        item = TestItem(
            id="L2-SCENARIO-001",
            layer=Layer.L2,
            dimensions=[Dimension.D1, Dimension.D2],
            language="python",
            difficulty=3,
            estimated_time_min=30,
            sandbox=SandboxConfig(image="python:3.12"),
            prompt_template="Add a search feature",
            scoring=ScoringConfig(type=ScoringType.LLM_JUDGE),
        )
        trace = AgentTrace(
            run_id="test",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L2-SCENARIO-001",
            start_time=datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 7, 1, 10, 30, 0, tzinfo=timezone.utc),
            final_output="Search implemented.",
        )

        judge = L2L3Judge()
        prompt = judge._build_prompt(item, trace, "--- main.py ---\ndef search(): pass\n")
        assert "Add a search feature" in prompt
        assert "test-agent" in prompt
        assert "Search implemented" in prompt

    @patch("httpx.Client")
    def test_score_success(self, mock_client_class):
        """Judge should parse the LLM response into score cards."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(SAMPLE_JUDGE_RESPONSE)}}]
        }
        mock_client_class.return_value.__enter__.return_value.post.return_value = mock_response

        item = TestItem(
            id="L2-SCENARIO-001",
            layer=Layer.L2,
            dimensions=[Dimension.D1, Dimension.D2],
            language="python",
            difficulty=3,
            estimated_time_min=30,
            sandbox=SandboxConfig(image="python:3.12"),
            prompt_template="Add search",
            scoring=ScoringConfig(type=ScoringType.LLM_JUDGE),
        )
        trace = AgentTrace(
            run_id="test",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L2-SCENARIO-001",
            start_time=datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 7, 1, 10, 30, 0, tzinfo=timezone.utc),
        )

        judge = L2L3Judge(api_key="test-key")
        result = judge.score(item, trace, "deliverables here")

        assert result.status == "completed"
        assert len(result.judge_score_cards) == 6
        assert any(c.dimension == Dimension.D1 and c.score == 4 for c in result.judge_score_cards)

    @patch("httpx.Client")
    def test_score_retry_on_failure(self, mock_client_class):
        """Judge should retry then fail after max retries."""
        mock_client_class.return_value.__enter__.return_value.post.side_effect = Exception("API error")

        item = TestItem(
            id="L2-SCENARIO-001",
            layer=Layer.L2,
            dimensions=[Dimension.D1],
            language="python",
            difficulty=3,
            estimated_time_min=30,
            sandbox=SandboxConfig(image="python:3.12"),
            prompt_template="Add search",
            scoring=ScoringConfig(type=ScoringType.LLM_JUDGE),
        )
        trace = AgentTrace(
            run_id="test",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L2-SCENARIO-001",
            start_time=datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 7, 1, 10, 30, 0, tzinfo=timezone.utc),
        )

        judge = L2L3Judge(api_key="test-key")
        result = judge.score(item, trace, "")

        assert result.status == "error"
        assert result.error_message is not None
