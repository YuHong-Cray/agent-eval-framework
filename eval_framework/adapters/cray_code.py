"""CrayCode adapter — drives CrayCode via CLI with trace parsing.

CrayCode is an AI coding agent that can be invoked via CLI.
This adapter captures full tool-call traces by parsing CrayCode's
structured output or verbose log format.
"""

import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCall, ToolCallStep


class CrayCodeAdapter(AgentAdapter):
    """Adapter for CrayCode AI coding agent.

    Drives CrayCode via CLI, capturing structured JSON traces when available,
    falling back to parsing verbose text output for tool calls.

    Supports two modes:
      - structured: CrayCode outputs JSON Lines of tool calls
      - verbose: Parse human-readable logs for tool call patterns
    """

    # Known CrayCode tool name patterns in verbose output
    TOOL_PATTERNS = {
        "Read": r"Reading\s+(?:file\s+)?(.+)",
        "Write": r"Writing\s+(?:file\s+)?(.+)",
        "Edit": r"Editing\s+(?:file\s+)?(.+)",
        "Bash": r"(?:Running|Executing)\s+command:\s*(.+)",
        "Grep": r"Searching\s+for\s+(.+?)\s+in\s+(.+)",
        "Glob": r"Finding\s+files\s+matching\s+(.+)",
        "Task": r"Dispatching\s+subagent:\s*(.+)",
    }

    def __init__(
        self,
        command: str = "cray",
        workspace: str = "",
        default_model: str = "deepseek-v4-pro",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        structured_output: bool = True,
        agent_name: str = "craycode",
        agent_version: str = "1.0",
    ):
        self._command = command
        self._workspace = workspace
        self._default_model = default_model
        self._api_key = api_key
        self._system_prompt = system_prompt
        self._structured_output = structured_output
        self._agent_name = agent_name
        self._agent_version = agent_version

    def execute(self, prompt: str, context: TestContext) -> AgentTrace:
        run_id = f"run-{context.test_item_id}-{int(time.time())}"
        start = datetime.now(timezone.utc)

        # Build CrayCode CLI args
        cmd = self._build_command(context)

        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=context.working_dir,
                timeout=context.layer_timeout_seconds(),
            )
        except subprocess.TimeoutExpired:
            # Return partial trace for timeout
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

        # Parse tool calls from output
        if self._structured_output:
            steps = self._parse_structured(proc.stdout)
        else:
            steps = self._parse_verbose(proc.stdout, proc.stderr)

        # Extract final output (non-tool content after last tool call)
        final_output = self._extract_final_output(proc.stdout)

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
            default_model=self._default_model,
        )

    def _build_command(self, context: TestContext) -> list[str]:
        """Build the CrayCode CLI command with appropriate flags."""
        cmd = [self._command]

        if self._structured_output:
            cmd.append("--output-format")
            cmd.append("json")

        if self._api_key:
            cmd.append("--api-key")
            cmd.append(self._api_key)

        if self._system_prompt:
            cmd.append("--system-prompt")
            cmd.append(self._system_prompt)

        if self._workspace:
            cmd.append("--workspace")
            cmd.append(self._workspace)

        cmd.append("--no-interactive")  # headless mode

        return cmd

    def _parse_structured(self, stdout: str) -> list[ToolCallStep]:
        """Parse JSON Lines tool call output from CrayCode.

        Expected format (one JSON object per line for tool calls):
          {"type":"tool_call","tool":"Read","params":{"file_path":"/x.py"},"result":{...},"ts":"...","duration_ms":150}
        """
        steps: list[ToolCallStep] = []
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") == "tool_call":
                ts = obj.get("ts")
                timestamp = (
                    datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if ts
                    else datetime.now(timezone.utc)
                )
                steps.append(
                    ToolCallStep(
                        step_index=len(steps),
                        tool_call=ToolCall(
                            tool_name=obj["tool"],
                            params=obj.get("params", {}),
                        ),
                        result=obj.get("result", {}),
                        timestamp=timestamp,
                        duration_ms=obj.get("duration_ms", 0),
                    )
                )
        return steps

    def _parse_verbose(
        self, stdout: str, stderr: str
    ) -> list[ToolCallStep]:
        """Parse human-readable CrayCode output for tool call patterns."""
        combined = stdout + "\n" + stderr
        steps: list[ToolCallStep] = []
        now = datetime.now(timezone.utc)

        for line in combined.split("\n"):
            for tool_name, pattern in self.TOOL_PATTERNS.items():
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    params = self._extract_params(tool_name, m)
                    steps.append(
                        ToolCallStep(
                            step_index=len(steps),
                            tool_call=ToolCall(
                                tool_name=tool_name,
                                params=params,
                            ),
                            result={},
                            timestamp=now,
                            duration_ms=0,
                        )
                    )
                    break
        return steps

    @staticmethod
    def _extract_params(tool_name: str, match: re.Match) -> dict:
        """Extract tool parameters from a regex match group."""
        if tool_name in ("Read", "Write", "Edit"):
            return {"file_path": match.group(1).strip()}
        elif tool_name == "Bash":
            return {"command": match.group(1).strip()}
        elif tool_name == "Grep":
            return {"pattern": match.group(1).strip(), "path": match.group(2).strip()}
        elif tool_name == "Glob":
            return {"pattern": match.group(1).strip()}
        elif tool_name == "Task":
            return {"prompt": match.group(1).strip()}
        return {}

    @staticmethod
    def _extract_final_output(stdout: str) -> str:
        """Extract the final message after all tool calls."""
        lines = stdout.strip().split("\n")
        # Walk backwards to find the last non-tool, non-JSON line
        final_lines = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "tool_call":
                    break  # Stop at last tool call
            except json.JSONDecodeError:
                final_lines.append(line)
            else:
                # JSON but not a tool call — could be final output
                if "final" in obj or "result" in obj:
                    final_lines.append(line)
                    break
        return "\n".join(reversed(final_lines))
