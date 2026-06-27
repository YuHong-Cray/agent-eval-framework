"""Task decomposition tree similarity for L1-D2 scoring."""

import json


class TreeSimilarity:
    @staticmethod
    def parse(json_str: str) -> dict:
        return json.loads(json_str)

    @staticmethod
    def compare(actual: dict, expected: dict) -> float:
        """Compute structural similarity between two task trees.

        Uses Jaccard similarity on flattened task names.
        """
        actual_tasks = TreeSimilarity._flatten(actual)
        expected_tasks = TreeSimilarity._flatten(expected)

        if not expected_tasks:
            return 1.0 if not actual_tasks else 0.0

        intersection = len(actual_tasks & expected_tasks)
        union = len(actual_tasks | expected_tasks)
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _flatten(tree: dict, depth: int = 0) -> set:
        tasks = {(tree.get("task", ""), depth)}
        for child in tree.get("subtasks", []):
            tasks |= TreeSimilarity._flatten(child, depth + 1)
        return tasks
