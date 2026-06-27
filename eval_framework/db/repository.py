"""Data access layer for evaluation results.

Thread-safe: all write methods acquire a global lock so that concurrent
SQLite access across ThreadPoolExecutor workers is serialized.
"""

import json
import threading
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from eval_framework.db.models import EvalResult, EvalRun, TraceRecord
from eval_framework.models import AgentTrace

# Global lock for serializing SQLite write operations across threads
_write_lock = threading.Lock()


class EvalRepository:
    def __init__(self, session: Session):
        self._session = session

    def save_run(self, trace: AgentTrace) -> EvalRun:
        """Save a completed evaluation run with its trace."""
        run = EvalRun(
            run_id=trace.run_id,
            agent_name=trace.agent_name,
            agent_version=trace.agent_version,
            test_item_id=trace.test_item_id,
            start_time=trace.start_time,
            end_time=trace.end_time,
            duration_seconds=trace.duration_seconds,
            status="completed",
        )
        trace_record = TraceRecord(
            run_id=trace.run_id,
            steps_json=json.dumps(
                [s.model_dump(mode="json") for s in trace.steps]
            ),
            final_output=trace.final_output,
        )
        self._session.add(run)
        self._session.add(trace_record)
        with _write_lock:
            try:
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise
        return run

    def get_run(self, run_id: str) -> Optional[EvalRun]:
        return (
            self._session.query(EvalRun)
            .filter(EvalRun.run_id == run_id)
            .first()
        )

    def list_runs(
        self,
        agent_name: Optional[str] = None,
        test_item_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[EvalRun]:
        q = self._session.query(EvalRun)
        if agent_name:
            q = q.filter(EvalRun.agent_name == agent_name)
        if test_item_id:
            q = q.filter(EvalRun.test_item_id == test_item_id)
        return (
            q.order_by(EvalRun.start_time.desc()).limit(limit).all()
        )

    def update_run_status(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        run = self.get_run(run_id)
        if run:
            run.status = status
            run.error_message = error_message
            with _write_lock:
                try:
                    self._session.commit()
                except Exception:
                    self._session.rollback()
                    raise

    def save_result(
        self,
        run_id: str,
        test_item_id: str,
        dimension: str,
        l1_score: Optional[float] = None,
        judge_score: Optional[int] = None,
        judge_reasoning: Optional[str] = None,
        status: str = "completed",
    ) -> EvalResult:
        result = EvalResult(
            run_id=run_id,
            test_item_id=test_item_id,
            dimension=dimension,
            l1_score=l1_score,
            judge_score=judge_score,
            judge_reasoning=judge_reasoning,
            status=status,
        )
        self._session.add(result)
        with _write_lock:
            try:
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise
        return result

    def get_agent_scores(
        self, agent_name: str, agent_version: Optional[str] = None
    ) -> dict[str, dict]:
        """Return per-dimension average scores for an agent.

        Priority: judge_score (1-5) is converted to 0-1 scale.
        l1_score is used as fallback. The 'combined' field gives the
        best available score on a 0-1 scale.
        """
        q = (
            self._session.query(
                EvalResult.dimension,
                func.avg(EvalResult.l1_score).label("avg_l1"),
                func.avg(EvalResult.judge_score).label("avg_judge"),
                func.count(EvalResult.id).label("count"),
            )
            .join(EvalRun, EvalResult.run_id == EvalRun.run_id)
            .filter(EvalRun.agent_name == agent_name)
        )
        if agent_version:
            q = q.filter(EvalRun.agent_version == agent_version)
        q = q.group_by(EvalResult.dimension)

        result = {}
        for dim, avg_l1, avg_judge, count in q.all():
            v_l1 = round(float(avg_l1), 3) if avg_l1 is not None else None
            v_judge = round(float(avg_judge), 1) if avg_judge is not None else None
            # Combined: prefer judge (scaled to 0-1), else l1
            if v_judge is not None:
                combined = round(v_judge / 5.0, 3)
            elif v_l1 is not None:
                combined = v_l1
            else:
                combined = 0.0

            result[dim] = {
                "avg_l1_score": v_l1,
                "avg_judge_score": v_judge,
                "combined_score": combined,
                "run_count": count,
            }
        return result
