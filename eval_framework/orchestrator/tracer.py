"""Agent execution trace capture and serialization."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from eval_framework.models import AgentTrace, ToolCall, ToolCallStep


class TraceCollector:
    """Collects agent tool-call steps and produces an AgentTrace."""

    def __init__(
        self,
        run_id: str,
        agent_name: str,
        agent_version: str,
        test_item_id: str,
    ):
        self.run_id = run_id
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.test_item_id = test_item_id
        self._start_time: Optional[datetime] = None
        self._steps: list[ToolCallStep] = []

    def start(self) -> None:
        """Mark the beginning of execution."""
        self._start_time = datetime.now(timezone.utc)

    def record_step(
        self,
        tool_call: ToolCall,
        result: dict,
        duration_ms: int,
    ) -> None:
        """Record a single tool invocation."""
        now = datetime.now(timezone.utc)
        self._steps.append(
            ToolCallStep(
                step_index=len(self._steps),
                tool_call=tool_call,
                result=result,
                timestamp=now,
                duration_ms=duration_ms,
            )
        )

    def finish(self, final_output: str = "") -> AgentTrace:
        """Close the trace and return the completed AgentTrace."""
        now = datetime.now(timezone.utc)
        return AgentTrace(
            run_id=self.run_id,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            test_item_id=self.test_item_id,
            start_time=self._start_time or now,
            end_time=now,
            steps=self._steps,
            final_output=final_output,
        )

    @staticmethod
    def save(trace: AgentTrace, path: Path) -> None:
        """Write trace to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(trace.model_dump_json(indent=2))

    @staticmethod
    def load(path: Path) -> AgentTrace:
        """Load trace from a JSON file."""
        return AgentTrace.model_validate_json(path.read_text())

    @staticmethod
    def save_to_dict(trace: AgentTrace) -> dict:
        """Convert trace to a flat dict for database insertion."""
        return {
            "run_id": trace.run_id,
            "agent_name": trace.agent_name,
            "agent_version": trace.agent_version,
            "test_item_id": trace.test_item_id,
            "start_time": trace.start_time,
            "end_time": trace.end_time,
            "steps_json": json.dumps(
                [s.model_dump(mode="json") for s in trace.steps]
            ),
            "final_output": trace.final_output,
            "duration_seconds": trace.duration_seconds,
        }
