"""Claude Code adapter — drives Claude Code via CLI.

Uses `claude -p <prompt> -d <dir> --output-format json --max-turns <n>`
to run Claude in non-interactive mode and parses the output for tool traces.
"""

import json
import os
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCall, ToolCallStep


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code via `claude` CLI.

    Invokes: claude -p "<prompt>" -d <dir> --output-format json --max-turns <n>
    Parses JSON stream output for tool calls.
    """

    # Fallback regex patterns for verbose output
    TOOL_PATTERNS = {
        "Read": r"Reading\s+(?:file\s+)?(.+)",
        "Write": r"Writing\s+(?:file\s+)?(.+)",
        "Edit": r"Editing\s+(?:file\s+)?(.+)",
        "Bash": r"(?:Running|Executing)\s+command:\s*(.+)",
        "Grep": r"Searching\s+for\s+(.+?)\s+in\s+(.+)",
        "Glob": r"Finding\s+files\s+matching\s+(.+)",
        "Task": r"(?:Dispatching|Launching)\s+(?:sub)?agent:\s*(.+)",
    }

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
        output = proc.stdout + "\n" + proc.stderr

        # Try JSON stream parsing first, fall back to verbose regex
        steps = self._parse_json_stream(output)
        if not steps:
            steps = self._parse_verbose(output)

        final_output = self._extract_final_output(output, steps)

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
            default_model=self._default_model or "claude-sonnet-4-6",
        )

    def _build_command(self, prompt: str, context: TestContext) -> str:
        """Build shell-safe command: claude -p <prompt> -d <dir> --max-turns <n>"""
        parts = [
            self._command,
            "-p", shlex.quote(prompt),
        ]

        dir_path = context.working_dir or self._workspace
        if dir_path:
            parts.extend(["-d", shlex.quote(dir_path)])

        parts.extend(["--max-turns", str(self._max_turns)])
        parts.extend(["--permission-mode", self._permission_mode])

        # Verbose for tool parsing (JSON stream format if available)
        parts.append("--output-format")
        parts.append("json")

        return " ".join(parts)

    def _parse_json_stream(self, output: str) -> list[ToolCallStep]:
        """Parse Claude Code JSON stream output.

        Claude Code outputs one JSON object per line for tool events:
          {"type":"tool_use","tool":"Read","input":{"file_path":"..."}}
          {"type":"tool_result","content":"..."}
        """
        steps: list[ToolCallStep] = []
        pending_tool: dict | None = None

        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") == "tool_use":
                pending_tool = {
                    "tool": obj.get("tool", obj.get("name", "unknown")),
                    "params": obj.get("input", obj.get("params", {})),
                    "ts": datetime.now(timezone.utc),
                }
            elif obj.get("type") == "tool_result" and pending_tool:
                raw_result = obj.get("content", {})
                if not isinstance(raw_result, dict):
                    raw_result = {"content": str(raw_result)}
                steps.append(
                    ToolCallStep(
                        step_index=len(steps),
                        tool_call=ToolCall(
                            tool_name=pending_tool["tool"],
                            params=pending_tool["params"],
                        ),
                        result=raw_result,
                        timestamp=pending_tool["ts"],
                        duration_ms=0,
                    )
                )
                pending_tool = None

        # Flush any pending tool without result
        if pending_tool:
            steps.append(
                ToolCallStep(
                    step_index=len(steps),
                    tool_call=ToolCall(
                        tool_name=pending_tool["tool"],
                        params=pending_tool["params"],
                    ),
                    result={},
                    timestamp=pending_tool["ts"],
                    duration_ms=0,
                )
            )

        return steps

    def _parse_verbose(self, output: str) -> list[ToolCallStep]:
        """Fallback: regex parse human-readable output."""
        steps: list[ToolCallStep] = []
        now = datetime.now(timezone.utc)

        for line in output.split("\n"):
            for tool_name, pattern in self.TOOL_PATTERNS.items():
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    params = self._extract_params(tool_name, m)
                    steps.append(
                        ToolCallStep(
                            step_index=len(steps),
                            tool_call=ToolCall(tool_name=tool_name, params=params),
                            result={},
                            timestamp=now,
                            duration_ms=0,
                        )
                    )
                    break
        return steps

    @staticmethod
    def _extract_params(tool_name: str, match: re.Match) -> dict:
        if tool_name in ("Read", "Write", "Edit"):
            return {"file_path": match.group(1).strip()}
        elif tool_name == "Bash":
            return {"command": match.group(1).strip()}
        elif tool_name == "Grep":
            return {"pattern": match.group(1).strip(), "path": match.group(2).strip() if match.lastindex and match.lastindex >= 2 else ""}
        elif tool_name == "Glob":
            return {"pattern": match.group(1).strip()}
        elif tool_name in ("Task", "Agent"):
            return {"prompt": match.group(1).strip()}
        return {}

    @staticmethod
    def _extract_final_output(output: str, steps: list[ToolCallStep]) -> str:
        """Extract final assistant message after last tool call."""
        lines = output.strip().split("\n")
        final_lines = []
        for line in reversed(lines):
            stripped = line.strip()
            if not stripped:
                if final_lines:
                    break
                continue
            try:
                obj = json.loads(stripped)
                if obj.get("type") in ("tool_use", "tool_result"):
                    break
                if "final" in obj or "result" in obj:
                    final_lines.append(stripped)
                    break
            except json.JSONDecodeError:
                final_lines.append(stripped)
        return "\n".join(reversed(final_lines))
