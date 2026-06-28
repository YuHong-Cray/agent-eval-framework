"""Generic CLI adapter — drives any agent that accepts prompt via stdin."""

import subprocess
import time
from datetime import datetime, timezone

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace


class CLIAdapter(AgentAdapter):
    """Drives an agent invoked via CLI, sending prompt on stdin.

    The agent is expected to write its final output to stdout.
    NOTE: This adapter cannot capture individual tool-call steps;
    it only records the start/end and final output. For full trace
    capture, use an agent-specific adapter like CrayCodeAdapter.
    """

    def __init__(
        self,
        command,
        workspace: str,
        default_model: str = "",
        supported_tools: list[str] | None = None,
        agent_name: str = "cli-generic",
        agent_version: str = "1.0",
    ):
        self._command = command  # str or list[str]
        self._use_shell = isinstance(command, str)
        self._workspace = workspace
        self._default_model = default_model
        self._supported_tools = supported_tools or []
        self._agent_name = agent_name
        self._agent_version = agent_version

    def execute(self, prompt: str, context: TestContext) -> AgentTrace:
        run_id = f"run-{context.test_item_id}-{int(time.time())}"
        start = datetime.now(timezone.utc)

        import os
        merged_env = {**os.environ, **context.env_vars}

        proc = subprocess.run(
            self._command,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=self._use_shell,
            cwd=context.working_dir,
            env=merged_env,
            timeout=context.layer_timeout_seconds(),
        )

        end = datetime.now(timezone.utc)
        return AgentTrace(
            run_id=run_id,
            agent_name=self._agent_name,
            agent_version=self._agent_version,
            test_item_id=context.test_item_id,
            start_time=start,
            end_time=end,
            steps=[],
            final_output=proc.stdout,
        )

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_name=self._agent_name,
            agent_version=self._agent_version,
            supported_tools=self._supported_tools,
            default_model=self._default_model,
        )
