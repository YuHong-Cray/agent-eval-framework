"""Test execution scheduler — stable serial execution for all layers.

Each _run_single_item creates a fresh DB session so SQLite works correctly.
"""

import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

# Bump recursion limit for Pydantic serialization of large traces
sys.setrecursionlimit(10000)

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.config import config
from eval_framework.db.connection import get_session
from eval_framework.db.repository import EvalRepository
from eval_framework.models import Layer, TestItem, TestResult
from eval_framework.orchestrator.context import ContextPreparer, TestItemRegistry
from eval_framework.orchestrator.tracer import TraceCollector
from eval_framework.sandbox.manager import SandboxManager
from eval_framework.scoring.l1_runner import L1Scorer
from eval_framework.scoring.l2_l3_judge import L2L3Judge


class Scheduler:
    """Orchestrates evaluation runs across layers — serial, stable execution."""

    def __init__(
        self,
        adapter: AgentAdapter,
        repository: Optional[EvalRepository] = None,
        registry: Optional[TestItemRegistry] = None,
        sandbox: Optional[SandboxManager] = None,
        judge: Optional[L2L3Judge] = None,
    ):
        self._adapter = adapter
        self._registry = registry or TestItemRegistry()
        self._sandbox = sandbox
        self._judge = judge or L2L3Judge()
        self._scorer = L1Scorer(judge=self._judge)
        self._preparer = ContextPreparer(self._registry)

    def _get_repo(self) -> EvalRepository:
        return EvalRepository(get_session())

    def run_layer(
        self,
        layer: str,
        items: Optional[list[TestItem]] = None,
    ) -> list[TestResult]:
        """Run all items for a given layer serially. Returns results."""
        if items is None:
            items = self._registry.get_by_layer(layer)

        results: list[TestResult] = []
        total = len(items)

        for i, item in enumerate(items):
            print(f"  [{i+1}/{total}] {item.id}")
            try:
                result = self._run_single_item(item)
                results.append(result)
            except Exception as e:
                caps = self._adapter.capabilities()
                results.append(
                    TestResult(
                        test_item_id=item.id,
                        agent_name=caps.agent_name,
                        agent_version=caps.agent_version,
                        layer=item.layer,
                        dimensions=item.dimensions,
                        status="error",
                        error_message=str(e),
                    )
                )

        return results

    def _run_single_item(self, item: TestItem) -> TestResult:
        """Execute one test item: prepare → run → score → persist."""
        caps = self._adapter.capabilities()
        collector = TraceCollector(
            run_id=f"run-{item.id}-{uuid.uuid4().hex[:8]}",
            agent_name=caps.agent_name,
            agent_version=caps.agent_version,
            test_item_id=item.id,
        )
        repo = self._get_repo()

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                workspace = Path(tmp_dir)
                self._preparer.prepare_workspace(item.id, workspace)

                context = TestContext(
                    test_item_id=item.id,
                    layer=item.layer,
                    dimensions=item.dimensions,
                    working_dir=str(workspace),
                    env_vars=item.sandbox.env_vars,
                    network_allowed=item.sandbox.network != "none",
                )

                collector.start()
                trace = self._adapter.execute(item.prompt_template, context)
                trace.run_id = collector.run_id

                # Safety truncation
                trace.steps = trace.steps[:50]
                trace.final_output = (trace.final_output or "")[:5000]

                if item.layer == Layer.L1:
                    result = self._scorer.score(item, trace, str(workspace))
                else:
                    result = self._judge.score(
                        item, trace,
                        self._collect_deliverables(item, workspace),
                    )

                repo.save_run(trace)

                judge_map = {}
                if result.judge_score_cards:
                    for card in result.judge_score_cards:
                        judge_map[card.dimension.value] = card.score

                for dim in result.dimensions:
                    repo.save_result(
                        run_id=result.run_id,
                        test_item_id=result.test_item_id,
                        dimension=dim.value,
                        l1_score=result.l1_score,
                        judge_score=judge_map.get(dim.value),
                    )

                return result

        except Exception as e:
            trace = collector.finish(f"Error: {e}")
            try:
                repo.save_run(trace)
                for dim in item.dimensions:
                    repo.save_result(
                        run_id=collector.run_id,
                        test_item_id=item.id,
                        dimension=dim.value,
                        l1_score=0.0,
                        status="error",
                    )
            except Exception:
                pass
            return TestResult(
                test_item_id=item.id,
                agent_name=caps.agent_name,
                agent_version=caps.agent_version,
                layer=item.layer,
                dimensions=item.dimensions,
                status="error",
                error_message=str(e),
                run_id=collector.run_id,
            )

    @staticmethod
    def _collect_deliverables(item: TestItem, workspace: Path) -> str:
        parts = []
        for rel in item.expected_artifacts:
            path = workspace / rel
            if path.exists():
                parts.append(f"--- {rel} ---\n{path.read_text()}\n")
        return "\n".join(parts) if parts else "(no deliverables found)"
