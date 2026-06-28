"""Claude Code adapter — drives Claude via `claude -p`.

Claude outputs NDJSON: one JSON object per line with type=result at end.
We use regex to extract the result text and tool names, avoiding deep json.loads.
"""

import json
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCall, ToolCallStep

# Instruction prepended to ALL prompts to force tool use in --print mode
_CRITICAL_INSTRUCTION = """CRITICAL: You MUST use your tools (Read, Write, Edit, Bash, Grep, Glob) to actually DO the work.
DO NOT just describe what you would do — actually execute the tools!
- Use Read to see file contents before editing
- Use Write to create new files with the required code
- Use Edit to modify existing files
- Use Bash to run tests and verify your work
- Use Grep/Glob to search for patterns in files

The working directory contains all the files mentioned in the task.
"""


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code via `claude` CLI.

    Uses --permission-mode acceptEdits so Write/Edit tools auto-execute
    in non-interactive --print mode.  Bash still requires interactive
    approval, but the eval harness runs tests itself via L1Scorer.
    """

    def __init__(
        self,
        command: str = "claude",
        workspace: str = "",
        default_model: str = "",
        max_turns: int = 50,
        permission_mode: str = "acceptEdits",
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

        # Augment prompt with tool-use instructions + workspace listing
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
        raw = (proc.stdout + "\n" + proc.stderr)[-100000:]  # last 100KB

        # Extract result — try structured first, then fall back to raw text
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

    @staticmethod
    def _augment_prompt(prompt: str, working_dir: str) -> str:
        """Add workspace context and tool-use instructions."""
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

        return (
            f"{_CRITICAL_INSTRUCTION}\n"
            f"{file_list}"
            f"TASK:\n"
            f"{prompt}\n\n"
            f"IMPORTANT: When the task asks for structured output (like JSON trees, code, etc.), "
            f"include it DIRECTLY in your final response. Do NOT only write it to a file.\n"
            f"If the task expects a specific format in the answer, output it inline."
        )

    def _build_command(self, prompt: str, context: TestContext) -> str:
        # Collapse newlines (shell splits on them) and escape for double-quote wrapping
        safe_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')
        safe_prompt = safe_prompt.replace("\n", " ").replace("\r", " ")

        parts = [self._command, "-p", f'"{safe_prompt}"']
        dir_path = context.working_dir or self._workspace
        if dir_path:
            parts.extend(["-d", shlex.quote(dir_path)])
        parts.extend(["--max-turns", str(self._max_turns)])
        # stream-json + verbose emits per-line tool_use events for step capture
        parts.extend(["--output-format", "stream-json", "--verbose"])
        parts.extend(["--permission-mode", self._permission_mode])
        return " ".join(parts)

    @staticmethod
    def _extract_result(raw: str) -> str:
        """Extract result text from Claude stream-json output.

        In stream-json mode, the final line is {"type":"result","result":"<text>"}
        We parse each NDJSON line safely (small objects, no recursion risk).
        """
        result_text = raw[-2000:]  # fallback
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "result":
                    text = obj.get("result", "")
                    if text:
                        result_text = text
            except json.JSONDecodeError:
                pass
        return result_text[:5000]

    @staticmethod
    def _extract_steps(raw: str) -> list[ToolCallStep]:
        """Extract tool_use events from Claude stream-json lines.

        Parses lines like:
          {"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read",...}],...}}
        Safe: each line is a small JSON object — no Pydantic recursion risk.
        """
        now = datetime.now(timezone.utc)
        steps: list[ToolCallStep] = []
        seen: set[str] = set()

        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # type=assistant may have message.content[] with tool_use entries
            if obj.get("type") == "assistant":
                msg = obj.get("message", {})
                for content in msg.get("content", []):
                    if content.get("type") == "tool_use":
                        name = content.get("name", "Bash").capitalize()
                        if len(steps) == 0 or steps[-1].tool_call.tool_name != name:
                            seen.add(name)
                            steps.append(ToolCallStep(
                                step_index=len(steps),
                                tool_call=ToolCall(tool_name=name, params={}),
                                result={}, timestamp=now, duration_ms=0,
                            ))
                            if len(steps) >= 100:
                                return steps

        # Fallback: count NDJSON tool_use occurrences
        if not steps:
            tool_count = raw.count('"tool_use"')
            if tool_count > 0:
                tool_count = min(tool_count, 100)
                steps = [
                    ToolCallStep(step_index=i, tool_call=ToolCall(tool_name="Bash", params={}),
                                 result={}, timestamp=now, duration_ms=0)
                    for i in range(min(tool_count, 50))
                ]

        return steps
