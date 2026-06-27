"""LLM-as-Judge scoring for L2 and L3 test items."""

import json
import os
from typing import Optional

import httpx

from eval_framework.config import config
from eval_framework.models import (
    AgentTrace,
    Dimension,
    JudgeScoreCard,
    TestItem,
    TestResult,
)

# ── Judge prompt template ──────────────────────────────

JUDGE_SYSTEM_PROMPT = """You are an objective evaluator of coding agent performance.
Score the agent on the specified dimensions on a scale of 1-5.

Scoring rubric:
1 = Severe defects, deliverable unusable
2 = Barely usable, core functionality partially implemented with notable issues
3 = Meets baseline, core functionality correctly implemented, no major defects
4 = Exceeds expectations, comprehensive implementation with good edge-case handling
5 = Excellent, output can be considered a best-practice exemplar, shows deep understanding

You MUST output ONLY valid JSON with NO markdown wrapping, NO code fences. Exactly this format:
{"scores":[{"dimension":"D1","score":3,"reasoning":"why"},{"dimension":"D2","score":4,"reasoning":"why"},...]}
"""

_JUDGE_USER_TEMPLATE = """Test Scenario: {scenario}

Agent: {agent} v{version}
Duration: {duration:.1f}s

Tool Calls:
{tools}

Agent Output:
{output}

Deliverables:
{deliverables}

Score the agent on {dims}. Output JSON exactly as specified.
Dimension definitions:
- D1 (Code Generation): correctness, completeness, edge-case handling, code quality
- D2 (Task Decomposition): breakdown granularity, dependency awareness, prioritization
- D3 (Tool Use): correct tool selection, parameter accuracy, chaining/sequencing
- D4 (Multi-Agent Collaboration): sub-agent dispatch quality, result integration, consistency
- D5 (Debugging/Review): bug detection rate, root-cause accuracy, fix correctness
- D6 (Memory/Context): cross-turn context retention, feedback responsiveness"""


class L2L3Judge:
    """Scores L2/L3 test results using DeepSeek-V4-Flash as judge."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        cfg = config.get_scoring_config().get("l2_l3", {})
        self._model = cfg.get("judge_model", "deepseek-v4-flash")
        self._api_base = api_base or cfg.get(
            "judge_api_base", "https://api.deepseek.com"
        )
        self._api_key = (
            api_key
            or cfg.get("api_key", "")
            or os.environ.get("EVAL_JUDGE_API_KEY", "")
            or os.environ.get("DEEPSEEK_API_KEY", "")
        )
        self._max_retries = cfg.get("judge_max_retries", 3)

    def score(
        self,
        item: TestItem,
        trace: AgentTrace,
        deliverables: str,
    ) -> TestResult:
        """Submit trace and deliverables to LLM judge, return scored result."""
        if not self._api_key:
            return TestResult(
                test_item_id=item.id,
                agent_name=trace.agent_name,
                agent_version=trace.agent_version,
                layer=item.layer,
                dimensions=item.dimensions,
                status="skipped",
                run_id=trace.run_id,
                error_message="No EVAL_JUDGE_API_KEY configured.",
            )

        dims = ", ".join(d.value for d in item.dimensions)
        prompt = _JUDGE_USER_TEMPLATE.format(
            scenario=item.prompt_template,
            agent=trace.agent_name,
            version=trace.agent_version,
            duration=trace.duration_seconds,
            tools=self._format_tool_calls(trace.steps),
            output=trace.final_output,
            deliverables=deliverables,
            dims=dims,
        )

        for attempt in range(self._max_retries):
            try:
                response = self._call_judge(prompt)
                scores = self._parse_response(response)
                if scores:
                    return TestResult(
                        test_item_id=item.id,
                        agent_name=trace.agent_name,
                        agent_version=trace.agent_version,
                        layer=item.layer,
                        dimensions=item.dimensions,
                        judge_score_cards=scores,
                        status="completed",
                        run_id=trace.run_id,
                    )
                # Empty scores — retry
                if attempt == self._max_retries - 1:
                    return TestResult(
                        test_item_id=item.id,
                        agent_name=trace.agent_name,
                        agent_version=trace.agent_version,
                        layer=item.layer,
                        dimensions=item.dimensions,
                        status="error",
                        run_id=trace.run_id,
                        error_message=f"Judge returned no scores. Raw: {response[:200]}",
                    )
            except Exception as e:
                if attempt == self._max_retries - 1:
                    return TestResult(
                        test_item_id=item.id,
                        agent_name=trace.agent_name,
                        agent_version=trace.agent_version,
                        layer=item.layer,
                        dimensions=item.dimensions,
                        status="error",
                        run_id=trace.run_id,
                        error_message=str(e),
                    )

        raise RuntimeError("Judge failed")

    @staticmethod
    def _format_tool_calls(steps) -> str:
        if not steps:
            return "(none)"
        lines = []
        for s in steps:
            tool = s.tool_call.tool_name
            params = json.dumps(s.tool_call.params, ensure_ascii=False)
            lines.append(f"  [{s.step_index}] {tool}({params}) — {s.duration_ms}ms")
        return "\n".join(lines)

    def _call_judge(self, prompt: str) -> str:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{self._api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_response(response: str) -> list[JudgeScoreCard]:
        """Parse judge response. Handles both flat {D1:1,...} and array {scores:[...]} formats."""
        text = response.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:]) if len(lines) > 1 else text
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        data = json.loads(text)

        # Format 1: {"scores": [{"dimension":"D1","score":3,"reasoning":"..."}, ...]}
        if "scores" in data:
            return [
                JudgeScoreCard(
                    dimension=Dimension(s["dimension"]),
                    score=int(s["score"]),
                    reasoning=s.get("reasoning", ""),
                )
                for s in data["scores"]
            ]

        # Format 2: {"D1": 3, "D2": 4, ...} — flat dimension→score
        cards = []
        for d in Dimension:
            key = d.value
            if key in data and isinstance(data[key], (int, float)):
                cards.append(
                    JudgeScoreCard(
                        dimension=d,
                        score=int(data[key]),
                        reasoning="",
                    )
                )
        if cards:
            return cards

        # Format 3: {"dimension":"D1","score":3} — single object
        if "dimension" in data and "score" in data:
            return [
                JudgeScoreCard(
                    dimension=Dimension(data["dimension"]),
                    score=int(data["score"]),
                    reasoning=data.get("reasoning", ""),
                )
            ]

        return []
