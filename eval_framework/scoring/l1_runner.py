"""L1 scoring coordinator — dispatches to appropriate scorer by type."""

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

    def score(
        self,
        item: TestItem,
        trace: AgentTrace,
        working_dir: str,
    ) -> TestResult:
        scoring = item.scoring
        l1_score: float = 0.0
        error_msg = None

        try:
            if scoring.type == ScoringType.UNIT_TEST:
                runner = TestRunnerFactory.get(item.language)
                test_result = runner.run(
                    working_dir=working_dir,
                    test_command=scoring.test_command,
                    pass_threshold=scoring.pass_threshold,
                )
                l1_score = test_result.score

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

            elif scoring.type == ScoringType.TREE_SIMILARITY:
                expected = TreeSimilarity.parse(scoring.expected_tree)
                try:
                    actual = TreeSimilarity.parse(trace.final_output)
                except Exception:
                    # Agent didn't output valid JSON — score 0 for this dimension
                    actual = {}
                l1_score = TreeSimilarity.compare(actual, expected)

            elif scoring.type == ScoringType.LLM_JUDGE:
                # L1 code-review items also use LLM judge; if no key, score 0
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
            status="completed",
            run_id=trace.run_id,
            error_message=error_msg,
        )
