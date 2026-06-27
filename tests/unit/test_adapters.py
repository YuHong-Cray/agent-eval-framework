"""Tests for Agent adapters."""
from pathlib import Path

import pytest

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.adapters.cli_generic import CLIAdapter
from eval_framework.adapters.factory import AdapterFactory
from eval_framework.models import AgentCapabilities, AgentTrace, Layer, Dimension


class TestAdapterFactory:
    def test_register_and_create(self):
        """Registering an adapter class should make it creatable."""
        AdapterFactory.register("test", CLIAdapter)
        adapter = AdapterFactory.create(
            "test",
            command="eval-agent run",
            workspace="/tmp/eval",
        )
        assert isinstance(adapter, CLIAdapter)

    def test_create_unregistered_raises(self):
        """Creating an unregistered adapter should raise."""
        with pytest.raises(KeyError):
            AdapterFactory.create("nonexistent", command="")


class TestCLIAdapter:
    def test_capabilities(self):
        """CLIAdapter should report capabilities from constructor."""
        adapter = CLIAdapter(
            command="test-agent run",
            workspace="/tmp/eval",
            default_model="gpt-4",
            supported_tools=["read", "write", "execute"],
        )
        caps = adapter.capabilities()
        assert caps.agent_name == "cli-generic"
        assert caps.default_model == "gpt-4"
        assert "read" in caps.supported_tools

    def test_execute_runs_command(self, tmp_path):
        """CLIAdapter.execute should run the command with prompt on stdin."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Use shell=True compatible command for cross-platform
        adapter = CLIAdapter(
            command=["python", "-c", "import sys; sys.stdout.write(sys.stdin.read())"],
            workspace=str(workspace),
        )
        context = TestContext(
            test_item_id="L1-D1-PY-001",
            layer=Layer.L1,
            dimensions=[Dimension.D1],
            working_dir=str(workspace),
            env_vars={},
            network_allowed=False,
        )
        trace = adapter.execute("hello world", context)
        assert trace.test_item_id == "L1-D1-PY-001"
        assert trace.agent_name == "cli-generic"
        assert "hello world" in trace.final_output


class TestCrayCodeAdapter:
    def test_capabilities(self):
        """CrayCodeAdapter should report full capabilities with subagents."""
        from eval_framework.adapters.cray_code import CrayCodeAdapter
        adapter = CrayCodeAdapter(
            command="craycode",
            workspace="/tmp/eval",
            default_model="deepseek-v4-pro",
        )
        caps = adapter.capabilities()
        assert caps.agent_name == "craycode"
        assert caps.default_model == "deepseek-v4-pro"
        assert caps.uses_subagents is True
        assert caps.has_memory_across_sessions is True
        assert "Read" in caps.supported_tools
        assert "Task" in caps.supported_tools

    def test_parse_structured_output(self):
        """Should parse JSON Lines tool call output."""
        from eval_framework.adapters.cray_code import CrayCodeAdapter
        adapter = CrayCodeAdapter(structured_output=True)

        stdout = (
            '{"type":"tool_call","tool":"Read","params":{"file_path":"/a.py"},"result":{"content":"x=1"},"ts":"2026-07-01T10:00:00Z","duration_ms":100}\n'
            '{"type":"tool_call","tool":"Edit","params":{"file_path":"/a.py","old_string":"x=1","new_string":"x=2"},"result":{"success":true},"ts":"2026-07-01T10:00:01Z","duration_ms":200}\n'
            "The file has been updated successfully.\n"
        )
        steps = adapter._parse_structured(stdout)
        assert len(steps) == 2
        assert steps[0].tool_call.tool_name == "Read"
        assert steps[0].tool_call.params["file_path"] == "/a.py"
        assert steps[0].duration_ms == 100
        assert steps[1].tool_call.tool_name == "Edit"
        assert steps[1].duration_ms == 200

    def test_parse_verbose_output(self):
        """Should parse human-readable tool call patterns."""
        from eval_framework.adapters.cray_code import CrayCodeAdapter
        adapter = CrayCodeAdapter(structured_output=False)

        stdout = (
            "Reading file /src/main.py...\n"
            "Found 3 TODO items.\n"
            "Running command: pytest tests/ -v\n"
            "All tests passed.\n"
            "Dispatching subagent: fix the bug in utils.py\n"
        )
        steps = adapter._parse_verbose(stdout, "")
        assert len(steps) >= 3
        tool_names = [s.tool_call.tool_name for s in steps]
        assert "Read" in tool_names
        assert "Bash" in tool_names
        assert "Task" in tool_names


class TestTestContext:
    def test_context_creation(self):
        ctx = TestContext(
            test_item_id="L1-D1-PY-001",
            layer=Layer.L1,
            dimensions=[Dimension.D1, Dimension.D3],
            working_dir="/eval/sandbox",
            env_vars={"DEBUG": "1"},
            network_allowed=False,
        )
        assert ctx.test_item_id == "L1-D1-PY-001"
        assert len(ctx.dimensions) == 2
        assert ctx.layer_timeout_seconds() == 900
