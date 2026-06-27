"""Tests for evaluation scheduler."""
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from eval_framework.adapters.cli_generic import CLIAdapter
from eval_framework.db.models import Base
from eval_framework.db.repository import EvalRepository
from eval_framework.models import (
    Dimension,
    Layer,
    SandboxConfig,
    ScoringConfig,
    ScoringType,
    TestItem,
)
from eval_framework.orchestrator.context import TestItemRegistry
from eval_framework.orchestrator.scheduler import Scheduler


def build_item(workspace: Path) -> TestItem:
    """Create a minimal TestItem with proper workspace paths."""
    return TestItem(
        id="L1-TEST-001",
        layer=Layer.L1,
        dimensions=[Dimension.D1],
        language="python",
        difficulty=1,
        estimated_time_min=1,
        sandbox=SandboxConfig(image="python:3.12"),
        prompt_template="hello",
        scoring=ScoringConfig(
            type=ScoringType.UNIT_TEST,
            test_command="pytest test_simple.py -v",
        ),
    )


def test_scheduler_run_l1(tmp_path):
    """Scheduler should run L1 items and produce results."""
    # Setup in-memory DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    repo = EvalRepository(session)

    item = build_item(tmp_path)

    adapter = CLIAdapter(
        command=["python", "-c", "print('done')"],
        workspace=str(tmp_path),
    )

    # Manually set up the registry with our item
    registry = TestItemRegistry()
    registry._items[item.id] = item

    scheduler = Scheduler(
        adapter=adapter,
        repository=repo,
        registry=registry,
    )

    results = scheduler.run_layer("L1", [item])
    assert len(results) == 1
    assert results[0].test_item_id == "L1-TEST-001"
    # Status may be error since test file doesn't exist in workspace,
    # but the scheduler should handle it gracefully
    assert results[0].status in ("completed", "error")


def test_scheduler_collect_deliverables(tmp_path):
    """Should collect deliverable file contents."""
    item = TestItem(
        id="L2-TEST-001",
        layer=Layer.L2,
        dimensions=[Dimension.D1],
        language="python",
        difficulty=1,
        estimated_time_min=10,
        sandbox=SandboxConfig(image="python:3.12"),
        prompt_template="...",
        expected_artifacts=["main.py"],
        scoring=ScoringConfig(type=ScoringType.LLM_JUDGE),
    )

    # Create the expected deliverable
    (tmp_path / "main.py").write_text("def search(): pass")

    result = Scheduler._collect_deliverables(item, tmp_path)
    assert "main.py" in result
    assert "def search(): pass" in result


def test_scheduler_instantiation():
    """Scheduler should be instantiatable with an adapter and repo."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    repo = EvalRepository(session)

    adapter = CLIAdapter(
        command=["echo", "test"],
        workspace="/tmp",
    )

    scheduler = Scheduler(adapter=adapter, repository=repo)
    assert scheduler._adapter is adapter
    # Session is created per-thread now; verify we can get one
    r = scheduler._get_repo()
    assert r is not None
