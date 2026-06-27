"""L1 scoring coordinator — dispatches to appropriate scorer by type.

For tree_sim / tool_match / llm_judge items (D2, D3, D5 review),
uses the LLM-as-Judge if available, since non-interactive agents
don't produce the structured outputs these scoring types expect.
"""

from eval_framework.models import (
    AgentTrace,
    ScoringType,
    TestItem,
    TestResult,
)
from eval_framework.scoring.test_runner import TestRunnerFactory
from eval_framework.scoring.tool_matcher import ToolMatcher
from eval_framework.scoring.tree_similarity import TreeSimilarity


class L1Scorer:
    """Coordinates L1 automated scoring for a single test item."""

    def __init__(self, judge=None):
        self._judge = judge

    def score(
        self,
        item: TestItem,
        trace: AgentTrace,
        working_dir: str,
    ) -> TestResult:
        scoring = item.scoring
        l1_score: float = 0.0
        error_msg = None
        judge_cards = []

        try:
            if scoring.type == ScoringType.UNIT_TEST:
                runner = TestRunnerFactory.get(item.language)
                test_result = runner.run(
                    working_dir=working_dir,
                    test_command=scoring.test_command,
                    pass_threshold=scoring.pass_threshold,
                )
                l1_score = test_result.score

            elif scoring.type == ScoringType.TREE_SIMILARITY:
                # Try native parsing first; if agent output is bad JSON,
                # fall back to LLM judge (or score 0)
                try:
                    expected = TreeSimilarity.parse(scoring.expected_tree)
                    actual = TreeSimilarity.parse(trace.final_output)
                    l1_score = TreeSimilarity.compare(actual, expected)
                except Exception:
                    l1_score = 0.0

                if l1_score == 0.0 and self._judge:
                    result = self._judge.score(
                        item, trace, trace.final_output
                    )
                    judge_cards = result.judge_score_cards
                    if judge_cards:
                        d2_card = next(
                            (c for c in judge_cards if c.dimension.value == "D2"),
                            judge_cards[0],
                        )
                        l1_score = d2_card.score / 5.0

            elif scoring.type == ScoringType.TOOL_MATCH:
                if scoring.tool_sequence:
                    seq_score = ToolMatcher.match_sequence(
                        trace.steps, scoring.tool_sequence
                    )
                    last_tool = (
                        scoring.tool_sequence[-1] if scoring.tool_sequence else ""
                    )
                    param_score = ToolMatcher.match_tool_params(
                        trace.steps, last_tool, scoring.key_params
                    )
                    l1_score = (seq_score + param_score) / 2
                else:
                    l1_score = ToolMatcher.match_tool_params(
                        trace.steps, "", scoring.key_params
                    )

                if l1_score == 0.0 and self._judge:
                    result = self._judge.score(
                        item, trace, trace.final_output
                    )
                    judge_cards = result.judge_score_cards
                    if judge_cards:
                        d3_card = next(
                            (c for c in judge_cards if c.dimension.value == "D3"),
                            judge_cards[0],
                        )
                        l1_score = d3_card.score / 5.0

            elif scoring.type == ScoringType.LLM_JUDGE:
                if self._judge:
                    result = self._judge.score(
                        item, trace, trace.final_output
                    )
                    judge_cards = result.judge_score_cards
                    if judge_cards:
                        l1_score = judge_cards[0].score / 5.0
                else:
                    l1_score = 0.0

        except Exception as e:
            l1_score = 0.0
            error_msg = str(e)

        return TestResult(
            test_item_id=item.id,
            agent_name=trace.agent_name,
            agent_version=trace.agent_version,
            layer=item.layer,
            dimensions=item.dimensions,
            l1_score=l1_score,
            judge_score_cards=judge_cards,
            status="completed",
            run_id=trace.run_id,
            error_message=error_msg,
        )
