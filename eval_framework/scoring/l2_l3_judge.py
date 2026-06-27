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

JUDGE_SYSTEM_PROMPT = """You are evaluating a coding agent's performance on a software engineering task.
Score ONLY the listed dimensions using the FULL 1-5 scale:
- 3 = competent, meets baseline expectations (DEFAULT for adequate work)
- 4 = exceeds expectations, handles edge cases well
- 5 = excellent, best-practice quality
- 2 = partially implemented, notable gaps
- 1 = severely deficient or not attempted

Vary your scores per dimension — don't give identical scores unless genuinely equal.
Output ONLY flat JSON: {"D1":3,"D2":4} with dimension codes as keys and integer scores."""


class L2L3Judge:
    """Scores L2/L3 test results using DeepSeek-V4-Flash as judge."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        cfg = config.get_scoring_config().get("l2_l3", {})
        self._model = cfg.get("judge_model", "deepseek-v4-flash")
        self._api_base = api_base or cfg.get("judge_api_base", "https://api.deepseek.com")
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

        dim_list = ", ".join(d.value for d in item.dimensions)

        # Build detailed dimension descriptions relevant to this item
        dim_descs = []
        for d in item.dimensions:
            if d == Dimension.D1:
                dim_descs.append(f"- D1 (Code): Is the generated code correct, complete, and well-structured?")
            elif d == Dimension.D2:
                dim_descs.append(f"- D2 (Decompose): Did the agent break the task into logical, well-ordered subtasks?")
            elif d == Dimension.D3:
                dim_descs.append(f"- D3 (Tools): Did the agent select the right tools with correct parameters?")
            elif d == Dimension.D4:
                dim_descs.append(f"- D4 (Multi-Agent): Did the agent effectively dispatch and coordinate sub-agents?")
            elif d == Dimension.D5:
                dim_descs.append(f"- D5 (Debug): Did the agent accurately find, explain, and fix the issues?")
            elif d == Dimension.D6:
                dim_descs.append(f"- D6 (Memory): Did the agent maintain context and learn from prior turns/sessions?")

        tools_str = "(none)"
        if trace.steps:
            lines = []
            for s in trace.steps:
                params = json.dumps(s.tool_call.params, ensure_ascii=False)
                lines.append(f"  [{s.step_index}] {s.tool_call.tool_name}({params})")
            tools_str = "\n".join(lines)

        prompt = f"""TASK: {item.prompt_template}

AGENT: {trace.agent_name} v{trace.agent_version}
TIME: {trace.duration_seconds:.1f}s

TOOL CALLS:
{tools_str}

AGENT OUTPUT:
{trace.final_output[:2000]}

DELIVERABLES:
{deliverables[:2000]}

Score ONLY these dimensions: {dim_list}
{"".join(dim_descs)}

Output ONLY flat JSON: {{"D2":3,"D3":4}}"""

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
                if attempt == self._max_retries - 1:
                    return TestResult(
                        test_item_id=item.id,
                        agent_name=trace.agent_name,
                        agent_version=trace.agent_version,
                        layer=item.layer,
                        dimensions=item.dimensions,
                        status="error",
                        run_id=trace.run_id,
                        error_message=f"No scores in: {response[:200]}",
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
            return resp.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_response(response: str) -> list[JudgeScoreCard]:
        """Parse judge response. Supports:
        - {"scores":[{"dimension":"D1","score":3,"reasoning":"..."}]}
        - {"D1":3,"D2":4}  (flat, most common from DeepSeek)
        - ```json ... ``` wrapped
        """
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:]) if len(lines) > 1 else text
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        data = json.loads(text)

        # Format 1: {"scores": [...]}
        if "scores" in data and isinstance(data["scores"], list):
            return [
                JudgeScoreCard(dimension=Dimension(s["dimension"]), score=int(s["score"]), reasoning=s.get("reasoning", ""))
                for s in data["scores"]
            ]

        # Format 2: {"D1":3,"D2":4,...} — flat
        cards = []
        for d in Dimension:
            if d.value in data and isinstance(data[d.value], (int, float)):
                cards.append(JudgeScoreCard(dimension=d, score=int(data[d.value]), reasoning=""))
        return cards
