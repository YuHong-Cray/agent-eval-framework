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

FLAT_JUDGE_RESPONSE = '{"D1": 3, "D2": 2, "D3": 4, "D4": 1, "D5": 3, "D6": 1}'


class TestParseResponse:
    def test_parse_scores_array_format(self):
        """Should parse {"scores": [...]} format."""
        cards = L2L3Judge._parse_response(json.dumps(SAMPLE_JUDGE_RESPONSE))
        assert len(cards) == 6
        assert cards[0].dimension == Dimension.D1
        assert cards[0].score == 4
        assert cards[0].reasoning == "Good code quality."

    def test_parse_flat_dimension_format(self):
        """Should parse {"D1":3, "D2":2, ...} flat format (DeepSeek actual output)."""
        cards = L2L3Judge._parse_response(FLAT_JUDGE_RESPONSE)
        assert len(cards) == 6
        d1 = next(c for c in cards if c.dimension == Dimension.D1)
        assert d1.score == 3
        d6 = next(c for c in cards if c.dimension == Dimension.D6)
        assert d6.score == 1

    def test_parse_with_markdown_fences(self):
        """Should strip ``` fences before parsing."""
        response = '```json\n' + FLAT_JUDGE_RESPONSE + '\n```'
        cards = L2L3Judge._parse_response(response)
        assert len(cards) == 6

    def test_parse_empty_returns_empty(self):
        """Should return empty list for unrecognized format."""
        cards = L2L3Judge._parse_response('{"unknown": 1}')
        assert cards == []


class TestL2L3Judge:
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

    @patch("httpx.Client")
    def test_score_flat_format(self, mock_client_class):
        """Judge should handle flat dimension format (real DeepSeek output)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": FLAT_JUDGE_RESPONSE}}]
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
        result = judge.score(item, trace, "out")

        assert result.status == "completed"
        assert len(result.judge_score_cards) == 6

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
