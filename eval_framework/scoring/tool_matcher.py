"""Tool call trajectory matching for L1 scoring."""

from eval_framework.models import ToolCallStep


class ToolMatcher:
    @staticmethod
    def match_sequence(
        steps: list[ToolCallStep],
        expected_sequence: list[str],
    ) -> float:
        """Score how well the actual tool sequence matches expected.

        Returns a score 0.0 to 1.0.
        """
        actual_names = [s.tool_call.tool_name for s in steps]
        matches = 0
        for i, expected_name in enumerate(expected_sequence):
            if i < len(actual_names) and actual_names[i] == expected_name:
                matches += 1
        return (
            matches / len(expected_sequence) if expected_sequence else 1.0
        )

    @staticmethod
    def match_tool_params(
        steps: list[ToolCallStep],
        expected_tool: str,
        key_params: list[str],
    ) -> float:
        """Check if any step used the expected tool with required params.

        Returns 1.0 if at least one step has the tool AND all key params.
        """
        for step in steps:
            if step.tool_call.tool_name == expected_tool:
                if all(
                    p in step.tool_call.params for p in key_params
                ):
                    return 1.0
        return 0.0
