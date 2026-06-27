"""Tests for database repository."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from eval_framework.db.models import Base, EvalResult
from eval_framework.db.repository import EvalRepository
from eval_framework.models import AgentTrace, ToolCall, ToolCallStep


@pytest.fixture
def session():
    """In-memory SQLite for fast testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def repo(session):
    return EvalRepository(session)


@pytest.fixture
def sample_trace():
    return AgentTrace(
        run_id="test-run-001",
        agent_name="craycode",
        agent_version="1.0",
        test_item_id="L1-D1-PY-001",
        start_time=datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 7, 1, 10, 5, 0, tzinfo=timezone.utc),
        steps=[
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(
                    tool_name="Read",
                    params={"file_path": "/src/main.py"},
                ),
                result={"content": "def f(): pass"},
                timestamp=datetime(
                    2026, 7, 1, 10, 0, 30, tzinfo=timezone.utc
                ),
                duration_ms=150,
            ),
        ],
        final_output="Implemented the function.",
    )


class TestEvalRun:
    def test_create_run(self, repo, sample_trace):
        """Saving a trace should create an EvalRun record."""
        run = repo.save_run(sample_trace)
        assert run.run_id == "test-run-001"
        assert run.status == "completed"

    def test_get_run(self, repo, sample_trace):
        """Retrieving a saved run should restore the trace data."""
        repo.save_run(sample_trace)
        run = repo.get_run("test-run-001")
        assert run is not None
        assert run.agent_name == "craycode"

    def test_list_runs_by_agent(self, repo, sample_trace):
        """Listing runs should filter by agent name."""
        repo.save_run(sample_trace)
        runs = repo.list_runs(agent_name="craycode")
        assert len(runs) == 1
        runs2 = repo.list_runs(agent_name="nonexistent")
        assert len(runs2) == 0

    def test_update_run_status(self, repo, sample_trace):
        """Updating a run status should persist."""
        repo.save_run(sample_trace)
        repo.update_run_status(
            "test-run-001", "timed_out", "Command exceeded limit"
        )
        run = repo.get_run("test-run-001")
        assert run.status == "timed_out"
        assert run.error_message == "Command exceeded limit"

    def test_get_agent_scores(self, repo, sample_trace):
        """Computing average scores should aggregate per-agent."""
        repo.save_run(sample_trace)
        result = EvalResult(
            run_id="test-run-001",
            test_item_id="L1-D1-PY-001",
            dimension="D1",
            l1_score=0.9,
            status="completed",
        )
        repo._session.add(result)
        repo._session.commit()

        scores = repo.get_agent_scores("craycode")
        assert "D1" in scores
        assert scores["D1"]["avg_l1_score"] == 0.9
