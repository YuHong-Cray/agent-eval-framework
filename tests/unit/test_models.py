"""Tests for shared Pydantic models."""
from datetime import datetime

import pytest

from eval_framework.models import (
    AgentCapabilities,
    AgentTrace,
    Dimension,
    JudgeScoreCard,
    Layer,
    SandboxConfig,
    ScoringConfig,
    ScoringType,
    TestItem,
    TestResult,
    ToolCall,
    ToolCallStep,
)


class TestTestItem:
    def test_valid_test_item_from_json(self):
        """TestItem should parse from standard JSON metadata."""
        data = {
            "id": "L1-D1-PY-001",
            "layer": "L1",
            "dimensions": ["D1"],
            "sub_dimensions": [],
            "language": "python",
            "difficulty": 2,
            "estimated_time_min": 8,
            "tags": ["function", "string-manipulation"],
            "sandbox": {
                "image": "python:3.12",
                "dependencies": ["pytest"],
                "network": "none",
            },
            "prompt_template": "Write a function that...",
            "context_files": ["context/main.py"],
            "expected_artifacts": ["main.py"],
            "scoring": {
                "type": "unit_test",
                "test_command": "pytest tests/",
                "pass_threshold": 0.85,
            },
        }
        item = TestItem(**data)
        assert item.id == "L1-D1-PY-001"
        assert item.layer == Layer.L1
        assert item.dimensions == [Dimension.D1]
        assert item.difficulty == 2
        assert item.sandbox.image == "python:3.12"
        assert item.scoring.type == ScoringType.UNIT_TEST

    def test_invalid_dimension_raises(self):
        """TestItem should reject unknown dimensions."""
        data = {
            "id": "X",
            "layer": "L1",
            "dimensions": ["D99"],
            "language": "python",
            "difficulty": 1,
            "estimated_time_min": 5,
            "sandbox": {"image": "x", "dependencies": [], "network": "none"},
            "prompt_template": "...",
            "context_files": [],
            "expected_artifacts": [],
            "scoring": {
                "type": "unit_test",
                "test_command": "",
                "pass_threshold": 0.5,
            },
        }
        with pytest.raises(ValueError):
            TestItem(**data)

    def test_difficulty_range_enforced(self):
        """TestItem difficulty must be 1-5."""
        data = {
            "id": "X",
            "layer": "L1",
            "dimensions": ["D1"],
            "language": "python",
            "difficulty": 6,
            "estimated_time_min": 5,
            "sandbox": {"image": "x", "dependencies": [], "network": "none"},
            "prompt_template": "...",
            "context_files": [],
            "expected_artifacts": [],
            "scoring": {
                "type": "unit_test",
                "test_command": "",
                "pass_threshold": 0.5,
            },
        }
        with pytest.raises(ValueError):
            TestItem(**data)


class TestAgentTrace:
    def test_serialize_deserialize(self):
        """AgentTrace should round-trip through JSON."""
        trace = AgentTrace(
            run_id="run-001",
            agent_name="craycode",
            agent_version="1.0",
            test_item_id="L1-D1-PY-001",
            start_time=datetime(2026, 7, 1, 10, 0, 0),
            end_time=datetime(2026, 7, 1, 10, 8, 30),
            steps=[
                ToolCallStep(
                    step_index=0,
                    tool_call=ToolCall(
                        tool_name="Read",
                        params={"file_path": "/src/main.py"},
                    ),
                    result={"content": "def add(a,b): return a+b"},
                    timestamp=datetime(2026, 7, 1, 10, 0, 5),
                    duration_ms=150,
                ),
                ToolCallStep(
                    step_index=1,
                    tool_call=ToolCall(
                        tool_name="Edit",
                        params={
                            "file_path": "/src/main.py",
                            "old_string": "def add(a,b): return a+b",
                            "new_string": "def add(a, b):\n    return a + b",
                        },
                    ),
                    result={"success": True},
                    timestamp=datetime(2026, 7, 1, 10, 1, 0),
                    duration_ms=200,
                ),
            ],
        )
        j = trace.model_dump_json()
        restored = AgentTrace.model_validate_json(j)
        assert restored.run_id == "run-001"
        assert len(restored.steps) == 2
        assert restored.steps[0].tool_call.tool_name == "Read"
        assert restored.duration_seconds == 510


class TestJudgeScoreCard:
    def test_valid_score_ranges_enforced(self):
        """JudgeScoreCard scores must be 1-5."""
        with pytest.raises(ValueError):
            JudgeScoreCard(
                dimension=Dimension.D1,
                score=0,
                reasoning="Score must be >= 1",
            )
        with pytest.raises(ValueError):
            JudgeScoreCard(
                dimension=Dimension.D1,
                score=6,
                reasoning="Score must be <= 5",
            )

    def test_valid_score_card(self):
        card = JudgeScoreCard(
            dimension=Dimension.D1,
            score=4,
            reasoning="Code is correct and well-structured.",
        )
        assert card.score == 4
        assert card.dimension == Dimension.D1
