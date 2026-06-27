"""Claude Code adapter — drives Claude via `claude -p`.

Claude Code outputs a single JSON object per turn (not JSONL stream).
We parse the final `result` field as the agent output and extract
tool_use events from the verbose combined output.
"""

import json
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Optional

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCall, ToolCallStep

# Bump recursion limit for deeply nested JSON from Claude output
sys.setrecursionlimit(5000)


def _truncate_dict(obj, max_depth=5, max_str_len=5000):
    """Recursively truncate dict values to avoid recursion/deep copy issues."""
    if isinstance(obj, dict):
        if max_depth <= 0:
            return f"<truncated dict with {len(obj)} keys>"
        return {k: _truncate_dict(v, max_depth - 1, max_str_len) for k, v in obj.items()}
    elif isinstance(obj, list):
        if max_depth <= 0:
            return f"<truncated list of {len(obj)} items>"
        return [_truncate_dict(v, max_depth - 1, max_str_len) for v in obj[:50]]
    elif isinstance(obj, str) and len(obj) > max_str_len:
        return obj[:max_str_len] + "...<truncated>"
    return obj


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code via `claude` CLI.

    Runs: claude -p "<prompt>" -d <dir> --output-format json --max-turns <n>
    """

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
        raw_output = proc.stdout + "\n" + proc.stderr

        # Claude outputs a single JSON line with type=result at the end
        # Extract final text result + limit step count to avoid OOM
        final_output, steps = self._parse_output(raw_output)

        # Safety: limit steps to avoid huge traces
        if len(steps) > 200:
            steps = steps[:200]

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
                "Task", "WebSearch", "WebFetch",
            ],
            uses_subagents=True,
            has_memory_across_sessions=True,
            default_model=self._default_model or "claude-sonnet-4-6",
        )

    def _build_command(self, prompt: str, context: TestContext) -> str:
        """claude -p <prompt> -d <dir> --output-format json --max-turns N"""
        parts = [self._command, "-p", shlex.quote(prompt)]
        dir_path = context.working_dir or self._workspace
        if dir_path:
            parts.extend(["-d", shlex.quote(dir_path)])
        parts.extend(["--max-turns", str(self._max_turns)])
        parts.extend(["--output-format", "json"])
        # permission mode
        parts.extend(["--permission-mode", self._permission_mode])
        return " ".join(parts)

    def _parse_output(self, raw: str) -> tuple[str, list[ToolCallStep]]:
        """Parse Claude Code output into final text and tool steps.

        Claude outputs a final JSON line like: {"type":"result","result":"..."}
        Steps are reconstructed from text patterns (tool_use events aren't
        streamed in --output-format json mode in a parseable way).
        """
        final_output = ""
        steps: list[ToolCallStep] = []
        now = datetime.now(timezone.utc)

        # Try to find the final result JSON line
        for line in reversed(raw.split("\n")):
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") == "result":
                result_text = obj.get("result", "")
                if isinstance(result_text, str) and len(result_text) > 100:
                    final_output = result_text
                # Extract num_turns
                turns = obj.get("num_turns", 0)
                break

        # If no final result found, use last 2000 chars of raw output
        if not final_output:
            final_output = raw[-2000:] if len(raw) > 2000 else raw

        # Fallback: regex for tool mentions in output (approximate)
        tool_re = re.compile(
            r'(Read|Write|Edit|Bash|Grep|Glob|Task)\b.*?(?:["\']([^"\']+)["\'])',
            re.IGNORECASE,
        )
        for m in tool_re.finditer(raw):
            tool_name = m.group(1).capitalize()
            param_val = m.group(2) or ""
            params: dict = {}
            if tool_name in ("Read", "Write", "Edit"):
                if param_val:
                    params["file_path"] = param_val
            elif tool_name == "Bash":
                if param_val:
                    params["command"] = param_val
            elif tool_name == "Grep":
                params["pattern"] = param_val
            elif tool_name == "Glob":
                params["pattern"] = param_val

            steps.append(
                ToolCallStep(
                    step_index=len(steps),
                    tool_call=ToolCall(tool_name=tool_name, params=params),
                    result={},
                    timestamp=now,
                    duration_ms=0,
                )
            )

        return final_output, steps
