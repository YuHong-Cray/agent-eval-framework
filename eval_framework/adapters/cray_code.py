"""CrayCode adapter — drives Cray via CLI with trace parsing.

Cray is the AI coding agent CLI. This adapter invokes `cray --input <prompt>`
in non-interactive mode and parses the output to capture tool-call traces.
"""

import json
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCall, ToolCallStep


class CrayCodeAdapter(AgentAdapter):
    """Adapter for the Cray AI coding agent.

    Drives Cray via CLI in non-interactive mode (`cray --input <prompt>`),
    parsing verbose output (-v) to extract tool-call steps.

    Cray CLI reference:
      cray [options] [prompt]           → interactive mode
      cray --input <text> [options]     → non-interactive, send msg and exit
      Options: -m <model>, -d <dir>, -v (verbose), --max-turns <n>, -p <mode>
    """

    # Patterns for parsing cray -v output
    # cray shows: [Cray] [Permission] Headless auto-approve: allowing "tool_name"
    TOOL_ALLOW_PATTERN = re.compile(
        r'\[Cray\]\s*\[Permission\].*allowing\s+"(\w+)"', re.IGNORECASE
    )

    # Turn header: [Cray] [Turn N] model_name
    TURN_PATTERN = re.compile(
        r'\[Cray\]\s*\[Turn\s+(\d+)\]\s+(\S+)'
    )

    def __init__(
        self,
        command: str = "cray",
        workspace: str = "",
        default_model: str = "deepseek-v4-pro",
        max_turns: int = 50,
        permission_mode: str = "default",
        agent_name: str = "craycode",
        agent_version: str = "1.0",
    ):
        self._command = command
        self._workspace = workspace
        self._default_model = default_model
        self._max_turns = max_turns
        self._permission_mode = permission_mode
        self._agent_name = agent_name
        self._agent_version = agent_version

    def execute(self, prompt: str, context: TestContext) -> AgentTrace:
        run_id = f"run-{context.test_item_id}-{int(time.time())}"
        start = datetime.now(timezone.utc)

        # Build command with shlex.quote() for shell=True safety
        cmd = self._build_command(prompt, context)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=True,
                cwd=context.working_dir,
                timeout=context.layer_timeout_seconds(),
            )
        except subprocess.TimeoutExpired:
            return AgentTrace(
                run_id=run_id,
                agent_name=self._agent_name,
                agent_version=self._agent_version,
                test_item_id=context.test_item_id,
                start_time=start,
                end_time=datetime.now(timezone.utc),
                steps=[],
                final_output="[TIMEOUT]",
            )

        end = datetime.now(timezone.utc)
        output = proc.stdout + "\n" + proc.stderr

        # Parse tool calls from verbose output
        steps = self._parse_verbose(output)

        # The final output is everything after the last tool call line
        final_output = self._extract_final_output(output)

        return AgentTrace(
            run_id=run_id,
            agent_name=self._agent_name,
            agent_version=self._agent_version,
            test_item_id=context.test_item_id,
            start_time=start,
            end_time=end,
            steps=steps,
            final_output=final_output,
        )

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_name=self._agent_name,
            agent_version=self._agent_version,
            supported_tools=[
                "Read", "Write", "Edit", "Bash", "Grep", "Glob",
                "Task", "Agent", "WebSearch", "WebFetch",
            ],
            uses_subagents=True,
            has_memory_across_sessions=True,
            default_model=self._default_model,
        )

    def _build_command(self, prompt: str, context: TestContext) -> str:
        """Build a shell-safe Cray CLI command using shlex.quote().

        Produces: cray --input <quoted-prompt> -d <quoted-dir> ... -v

        Uses shlex.quote() on all user-controlled values to prevent command injection
        while still supporting Windows npm/.cmd wrappers that require shell=True.
        """
        parts = [self._command, "--input", shlex.quote(prompt)]

        dir_path = context.working_dir or self._workspace
        if dir_path:
            parts.extend(["-d", shlex.quote(dir_path)])

        if self._default_model:
            parts.extend(["-m", shlex.quote(self._default_model)])

        if self._max_turns:
            parts.extend(["--max-turns", str(self._max_turns)])

        if self._permission_mode:
            parts.extend(["-p", shlex.quote(self._permission_mode)])

        # Verbose mode for trace parsing
        parts.append("-v")

        return " ".join(parts)

    def _parse_verbose(self, output: str) -> list[ToolCallStep]:
        """Parse cray -v output for tool calls.

        cray outputs:
          [Cray] [Permission] Headless auto-approve: allowing "bash"
          [Cray] [Permission] Headless auto-approve: allowing "read"
          [Cray] [Turn 1] deepseek/deepseek-v4-flash
        """
        steps: list[ToolCallStep] = []
        now = datetime.now(timezone.utc)

        for line in output.split("\n"):
            m = self.TOOL_ALLOW_PATTERN.search(line)
            if m:
                tool_name = m.group(1).capitalize()
                steps.append(
                    ToolCallStep(
                        step_index=len(steps),
                        tool_call=ToolCall(
                            tool_name=tool_name,
                            params={},
                        ),
                        result={},
                        timestamp=now,
                        duration_ms=0,
                    )
                )
        return steps

    @staticmethod
    def _extract_final_output(output: str) -> str:
        """Extract the final agent message after all tool calls."""
        lines = output.strip().split("\n")
        # Walk backwards to find the last substantive output line
        final_lines = []
        for line in reversed(lines):
            stripped = line.strip()
            # Skip cray framework lines
            if not stripped or stripped.startswith("[Cray]"):
                if final_lines:
                    break
                continue
            final_lines.append(stripped)
        return "\n".join(reversed(final_lines))
