"""Integration test for L1 scoring."""
from datetime import datetime, timezone

from eval_framework.scoring.l1_runner import L1Scorer
from eval_framework.models import (
    AgentTrace,
    Dimension,
    Layer,
    SandboxConfig,
    ScoringConfig,
    ScoringType,
    TestItem,
)


def test_l1_unit_test_scoring(tmp_path):
    """L1Scorer should run pytest and compute score."""
    test_file = tmp_path / "test_math.py"
    test_file.write_text(
        """
def test_add():
    assert 1 + 2 == 3

def test_mul():
    assert 2 * 3 == 6
"""
    )

    item = TestItem(
        id="L1-D1-PY-001",
        layer=Layer.L1,
        dimensions=[Dimension.D1],
        language="python",
        difficulty=1,
        estimated_time_min=5,
        sandbox=SandboxConfig(
            image="python:3.12", dependencies=[], network="none"
        ),
        prompt_template="...",
        scoring=ScoringConfig(
            type=ScoringType.UNIT_TEST,
            test_command=f"pytest {test_file.name} -v",
            pass_threshold=0.85,
        ),
    )
    trace = AgentTrace(
        run_id="test",
        agent_name="test-agent",
        agent_version="1.0",
        test_item_id="L1-D1-PY-001",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
    )

    scorer = L1Scorer()
    result = scorer.score(item, trace, str(tmp_path))
    assert result.l1_score == 1.0
