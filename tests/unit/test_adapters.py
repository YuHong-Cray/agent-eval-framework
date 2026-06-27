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
            command="cray",
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

    def test_build_command(self):
        """Should build correct cray CLI command with --input flag."""
        from eval_framework.adapters.cray_code import CrayCodeAdapter
        from eval_framework.adapters.base import TestContext
        from eval_framework.models import Layer, Dimension

        adapter = CrayCodeAdapter(
            command="cray",
            default_model="deepseek-v4-pro",
        )
        ctx = TestContext(
            test_item_id="L1-TEST",
            layer=Layer.L1,
            dimensions=[Dimension.D1],
            working_dir="/tmp/eval",
        )
        cmd = adapter._build_command('say hello', ctx)
        assert "--input" in cmd
        assert "say hello" in cmd
        assert '-d' in cmd or '--dir' in cmd
        assert '-m "deepseek-v4-pro"' in cmd
        assert "-v" in cmd

    def test_parse_verbose_output(self):
        """Should parse cray permission lines for tool calls."""
        from eval_framework.adapters.cray_code import CrayCodeAdapter
        adapter = CrayCodeAdapter()

        stdout = (
            "[Cray] Initializing Cray Code...\n"
            '[Cray] [Turn 1] deepseek/deepseek-v4-flash\n'
            '  └── Thought: I need to read the file...\n'
            '[Cray] [Permission] Headless auto-approve: allowing "read"\n'
            '[Cray] [Turn 2] deepseek/deepseek-v4-flash\n'
            '  └── Thought: Now I should run the tests.\n'
            '  └── Running tools...\n'
            '[Cray] [Permission] Headless auto-approve: allowing "bash"\n'
            "All tests passed!\n"
        )
        steps = adapter._parse_verbose(stdout)
        assert len(steps) == 2
        assert steps[0].tool_call.tool_name == "Read"
        assert steps[1].tool_call.tool_name == "Bash"

    def test_extract_final_output(self):
        """Should extract only the agent's final response, not framework lines."""
        from eval_framework.adapters.cray_code import CrayCodeAdapter
        adapter = CrayCodeAdapter()

        stdout = (
            "[Cray] Initializing Cray Code...\n"
            '[Cray] [Turn 1] deepseek/deepseek-v4-flash\n'
            '  └── Thought: Let me implement this...\n'
            '[Cray] [Permission] Headless auto-approve: allowing "write"\n'
            "The function has been implemented.\n"
            "All edge cases are handled.\n"
            "[Cray] [Turn 2] deepseek/deepseek-v4-flash\n"
        )
        result = adapter._extract_final_output(stdout)
        assert "function has been implemented" in result
        assert "[Cray]" not in result


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
