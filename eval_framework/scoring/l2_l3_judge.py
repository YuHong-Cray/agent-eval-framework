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
Given a test scenario, the agent's execution trace, and its final deliverables,
score the agent on each of six dimensions on a scale of 1-5.

Scoring rubric:
1 = Severe defects, deliverable unusable
2 = Barely usable, core functionality partially implemented with notable issues
3 = Meets baseline, core functionality correctly implemented, no major defects
4 = Exceeds expectations, comprehensive implementation with good edge-case handling
5 = Excellent, output can be considered a best-practice exemplar, shows deep understanding

You MUST output valid JSON only — no markdown, no commentary outside JSON.
"""


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
        # Skip if no API key configured — return unscored result
        if not self._api_key:
            return TestResult(
                test_item_id=item.id,
                agent_name=trace.agent_name,
                agent_version=trace.agent_version,
                layer=item.layer,
                dimensions=item.dimensions,
                status="skipped",
                run_id=trace.run_id,
                error_message="No EVAL_JUDGE_API_KEY configured. Set env var or config.yaml scoring.l2_l3.api_key.",
            )

        prompt = self._build_prompt(item, trace, deliverables)

        for attempt in range(self._max_retries):
            try:
                response = self._call_judge(prompt)
                scores = self._parse_response(response)
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

        raise RuntimeError("Judge failed — should not reach here")

    def _build_prompt(
        self,
        item: TestItem,
        trace: AgentTrace,
        deliverables: str,
    ) -> str:
        return f"""Test Scenario: {item.prompt_template}

Agent: {trace.agent_name} v{trace.agent_version}
Duration: {trace.duration_seconds:.1f}s

Tool Calls Made:
{self._format_tool_calls(trace.steps)}

Final Output:
{trace.final_output}

Deliverables:
{deliverables}

Score the agent on all 6 dimensions (D1-D6). Output JSON per the schema."""

    @staticmethod
    def _format_tool_calls(steps) -> str:
        lines = []
        for s in steps:
            tool = s.tool_call.tool_name
            params = json.dumps(s.tool_call.params, ensure_ascii=False)
            lines.append(
                f"  [{s.step_index}] {tool}({params}) — {s.duration_ms}ms"
            )
        return "\n".join(lines) if lines else "(no tool calls)"

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
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_response(response: str) -> list[JudgeScoreCard]:
        data = json.loads(response)
        scores = data.get("scores", [])
        return [
            JudgeScoreCard(
                dimension=Dimension(s["dimension"]),
                score=s["score"],
                reasoning=s["reasoning"],
            )
            for s in scores
        ]
