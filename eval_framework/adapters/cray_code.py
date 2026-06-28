"""CrayCode adapter — drives Cray via CLI with trace parsing.

Wraps test item prompts with tool-usage instructions so that cray
in --input mode actually uses Read/Write/Edit/Bash to complete tasks
rather than just describing what it would do.
"""

import json
import os
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCall, ToolCallStep

# Instruction prepended to ALL prompts to force tool use in --input mode
_CRITICAL_INSTRUCTION = """CRITICAL: You MUST use your tools (Read, Write, Edit, Bash, Grep, Glob) to actually DO the work.
DO NOT just describe what you would do — actually do it with tools!
- Use Read to see file contents before editing
- Use Write to create new files with the required code
- Use Edit to modify existing files
- Use Bash to run tests and verify your work
- Use Grep to search for patterns in files

The working directory contains all the files mentioned in the task.
"""


class CrayCodeAdapter(AgentAdapter):
    """Adapter for the Cray AI coding agent.

    Invokes cray in non-interactive mode with tool-use instructions.
    """

    TOOL_ALLOW_PATTERN = re.compile(
        r'\[Cray\]\s*\[Permission\].*allowing\s+"(\w+)"', re.IGNORECASE
    )

    # Map thought keywords to tool names (for verbose mode without permission logs)
    _THOUGHT_TO_TOOL: dict[str, str] = {
        "read": "Read",
        "reading": "Read",
        "write": "Write",
        "writing": "Write",
        "edit": "Edit",
        "editing": "Edit",
        "modify": "Edit",
        "bash": "Bash",
        "run ": "Bash",
        "pytest": "Bash",
        "execute": "Bash",
        "grep": "Grep",
        "search": "Grep",
        "glob": "Glob",
    }

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

        # Augment prompt: list workspace files + force tool usage
        augmented = self._augment_prompt(prompt, context.working_dir)

        cmd = self._build_command(augmented, context)

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
        output = proc.stdout + "\n" + proc.stderr

        steps = self._parse_verbose(output)
        final_output = self._extract_final_output(output)

        return AgentTrace(
            run_id=run_id, agent_name=self._agent_name, agent_version=self._agent_version,
            test_item_id=context.test_item_id, start_time=start, end_time=end,
            steps=steps, final_output=final_output,
        )

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_name=self._agent_name, agent_version=self._agent_version,
            supported_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob",
                             "Task", "Agent", "WebSearch", "WebFetch"],
            uses_subagents=True, has_memory_across_sessions=True,
            default_model=self._default_model,
        )

    @staticmethod
    def _augment_prompt(prompt: str, working_dir: str) -> str:
        """Add workspace context and tool-use instructions."""
        # List workspace files
        file_list = ""
        ws = Path(working_dir)
        if ws.exists():
            files = []
            for p in sorted(ws.rglob("*")):
                if p.is_file() and ".git" not in str(p) and "__pycache__" not in str(p):
                    rel = str(p.relative_to(ws))
                    files.append(f"  {rel}")
            if files:
                file_list = "Available workspace files:\n" + "\n".join(files[:30]) + "\n\n"

        return f"{_CRITICAL_INSTRUCTION}\n{file_list}TASK:\n{prompt}"

    def _build_command(self, prompt: str, context: TestContext) -> str:
        # Use double-quote wrapping (Windows-compatible) with escaped inner quotes
        safe_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')
        # Collapse newlines — shell splits on them
        safe_prompt = safe_prompt.replace("\n", " ").replace("\r", " ")

        parts = [self._command, f'--input "{safe_prompt}"']

        dir_path = context.working_dir or self._workspace
        if dir_path:
            parts.extend(["-d", f'"{dir_path}"'])

        if self._default_model:
            parts.extend(["-m", self._default_model])

        if self._max_turns:
            parts.extend(["--max-turns", str(self._max_turns)])

        if self._permission_mode:
            parts.extend(["-p", self._permission_mode])

        parts.append("-v")
        return " ".join(parts)

    def _parse_verbose(self, output: str) -> list[ToolCallStep]:
        steps: list[ToolCallStep] = []
        now = datetime.now(timezone.utc)
        seen_tools: set[str] = set()

        # Strategy 1: Explicit permission/allow lines (cray -p default mode)
        for line in output.split("\n"):
            m = self.TOOL_ALLOW_PATTERN.search(line)
            if m:
                name = m.group(1).capitalize()
                seen_tools.add(name)
                steps.append(ToolCallStep(
                    step_index=len(steps),
                    tool_call=ToolCall(tool_name=name, params={}),
                    result={}, timestamp=now, duration_ms=0,
                ))

        # Strategy 2: Parse "Thought:" lines for tool intent keywords
        if not steps:
            for line in output.split("\n"):
                thought_match = re.search(
                    r"Thought:\s*(.*)", line, re.IGNORECASE
                )
                if not thought_match:
                    continue
                text = thought_match.group(1).lower()
                for keyword, tool_name in self._THOUGHT_TO_TOOL.items():
                    if keyword in text and tool_name not in seen_tools:
                        seen_tools.add(tool_name)
                        steps.append(ToolCallStep(
                            step_index=len(steps),
                            tool_call=ToolCall(tool_name=tool_name, params={}),
                            result={}, timestamp=now, duration_ms=0,
                        ))
                        # Only one tool per thought turn
                        break

        # Strategy 3: Each "Running tools..." + turn = at least one tool call
        if not steps:
            running_count = output.count("Running tools")
            turn_count = len(re.findall(r"\[Cray\]\s*\[Turn\s+\d+\]", output))
            tool_count = max(running_count, turn_count // 2)
            if tool_count > 0:
                for i in range(min(tool_count, 20)):
                    steps.append(ToolCallStep(
                        step_index=i,
                        tool_call=ToolCall(tool_name="Bash", params={}),
                        result={}, timestamp=now, duration_ms=0,
                    ))

        return steps[:100]

    @staticmethod
    def _extract_final_output(output: str) -> str:
        lines = output.strip().split("\n")
        final_lines = []
        for line in reversed(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("[Cray]"):
                if final_lines:
                    break
                continue
            final_lines.append(stripped)
        return "\n".join(reversed(final_lines))
