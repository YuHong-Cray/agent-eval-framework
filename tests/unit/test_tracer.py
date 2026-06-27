"""Tests for agent trace collection."""
import json
from pathlib import Path

import pytest

from eval_framework.models import AgentTrace, ToolCall, ToolCallStep
from eval_framework.orchestrator.tracer import TraceCollector


class TestTraceCollector:
    def test_start_and_record_step(self):
        """Collector should track start time and record steps."""
        collector = TraceCollector(
            run_id="test-001",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L1-D1-PY-001",
        )
        collector.start()
        collector.record_step(
            ToolCall(tool_name="Read", params={"file_path": "/x.py"}),
            {"content": "data"},
            150,
        )
        collector.record_step(
            ToolCall(
                tool_name="Edit",
                params={
                    "file_path": "/x.py",
                    "old_string": "a",
                    "new_string": "b",
                },
            ),
            {"success": True},
            200,
        )
        trace = collector.finish(final_output="done")

        assert trace.run_id == "test-001"
        assert len(trace.steps) == 2
        assert trace.steps[0].tool_call.tool_name == "Read"
        assert trace.steps[0].step_index == 0
        assert trace.steps[0].duration_ms == 150
        assert trace.steps[1].step_index == 1
        assert trace.steps[1].tool_call.tool_name == "Edit"
        assert trace.final_output == "done"
        assert trace.duration_seconds >= 0

    def test_save_and_load_trace(self, tmp_path):
        """Trace should round-trip through JSON file."""
        collector = TraceCollector(
            run_id="test-002",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L1-D1-PY-001",
        )
        collector.start()
        collector.record_step(
            ToolCall(tool_name="Bash", params={"command": "ls"}),
            {"stdout": "file1\nfile2"},
            100,
        )
        trace = collector.finish(final_output="listed files")

        filepath = tmp_path / "trace.json"
        collector.save(trace, filepath)

        loaded = TraceCollector.load(filepath)
        assert loaded.run_id == "test-002"
        assert len(loaded.steps) == 1
        assert loaded.steps[0].tool_call.tool_name == "Bash"

    def test_save_to_dict(self):
        """save_to_dict should return a plain dict for DB insertion."""
        collector = TraceCollector(
            run_id="test-003",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L1-D1-PY-001",
        )
        collector.start()
        collector.record_step(
            ToolCall(tool_name="Read", params={"file_path": "/z.py"}),
            {"content": "x=1"},
            50,
        )
        trace = collector.finish("ok")
        d = collector.save_to_dict(trace)

        assert d["run_id"] == "test-003"
        assert isinstance(d["steps_json"], str)
        steps = json.loads(d["steps_json"])
        assert steps[0]["tool_call"]["tool_name"] == "Read"
