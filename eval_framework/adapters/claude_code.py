"""Claude Code adapter — drives Claude via `claude -p`.

Claude outputs a single massive JSON line with type=result at end.
We use regex to extract the result text and avoid json.loads recursion.
"""

import json
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCall, ToolCallStep


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code via `claude` CLI."""

    def __init__(
        self,
        command: str = "claude",
        workspace: str = "",
        default_model: str = "",
        max_turns: int = 50,
        permission_mode: str = "default",
        agent_name: str = "claude",
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
                run_id=run_id, agent_name=self._agent_name, agent_version=self._agent_version,
                test_item_id=context.test_item_id, start_time=start,
                end_time=datetime.now(timezone.utc), steps=[], final_output="[TIMEOUT]",
            )

        end = datetime.now(timezone.utc)
        raw = (proc.stdout + "\n" + proc.stderr)[-20000:]  # last 20KB only

        # Extract result from Claude's JSON output
        final_output = self._extract_result(raw)
        steps = self._extract_steps(raw)

        return AgentTrace(
            run_id=run_id, agent_name=self._agent_name, agent_version=self._agent_version,
            test_item_id=context.test_item_id, start_time=start, end_time=end,
            steps=steps[:100], final_output=final_output[:5000],
        )

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_name=self._agent_name, agent_version=self._agent_version,
            supported_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task", "WebSearch", "WebFetch"],
            uses_subagents=True, has_memory_across_sessions=True,
            default_model=self._default_model or "claude-sonnet-4-6",
        )

    def _build_command(self, prompt: str, context: TestContext) -> str:
        parts = [self._command, "-p", shlex.quote(prompt)]
        dir_path = context.working_dir or self._workspace
        if dir_path:
            parts.extend(["-d", shlex.quote(dir_path)])
        parts.extend(["--max-turns", str(self._max_turns)])
        parts.extend(["--output-format", "json"])
        parts.extend(["--permission-mode", self._permission_mode])
        return " ".join(parts)

    @staticmethod
    def _extract_result(raw: str) -> str:
        """Extract result text from Claude JSON WITHOUT json.loads (avoids recursion)."""
        # Claude JSON has: "result":"<escaped text>",
        # Use regex to capture the result value
        m = re.search(r'"result"\s*:\s*"((?:[^"\\]|\\.)*)"', raw, re.DOTALL)
        if m:
            text = m.group(1)
            # Unescape JSON escapes
            text = text.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
            return text[:5000]
        # Fallback: last 2000 chars
        return raw[-2000:] if len(raw) > 2000 else raw

    @staticmethod
    def _extract_steps(raw: str) -> list[ToolCallStep]:
        """Count tool_use events via simple string matching (avoids json.loads)."""
        now = datetime.now(timezone.utc)
        # Count "type":"tool_use" occurrences
        tool_count = raw.count('"type":"tool_use"')
        if tool_count > 100:
            tool_count = 100

        # Also look for permission approvals (tool names)
        steps: list[ToolCallStep] = []
        for m in re.finditer(r'allowing\s+"(\w+)"', raw, re.IGNORECASE):
            steps.append(ToolCallStep(
                step_index=len(steps),
                tool_call=ToolCall(tool_name=m.group(1).capitalize(), params={}),
                result={}, timestamp=now, duration_ms=0,
            ))
        return steps[:100] if steps else [
            ToolCallStep(step_index=0, tool_call=ToolCall(tool_name="Bash", params={}), result={}, timestamp=now, duration_ms=0)
        ] * min(tool_count, 50)
