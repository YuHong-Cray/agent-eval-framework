"""Tests for tree_similarity."""
from eval_framework.scoring.tree_similarity import TreeSimilarity


class TestTreeSimilarity:
    def test_identical_trees(self):
        expected = {
            "task": "Add search",
            "subtasks": [
                {"task": "Design API", "subtasks": []},
                {"task": "Implement backend", "subtasks": []},
            ],
        }
        actual = {
            "task": "Add search",
            "subtasks": [
                {"task": "Design API", "subtasks": []},
                {"task": "Implement backend", "subtasks": []},
            ],
        }
        score = TreeSimilarity.compare(actual, expected)
        assert score == 1.0

    def test_different_structure(self):
        expected = {
            "task": "A",
            "subtasks": [
                {"task": "B", "subtasks": []},
                {"task": "C", "subtasks": []},
            ],
        }
        actual = {"task": "A", "subtasks": []}
        score = TreeSimilarity.compare(actual, expected)
        assert 0.0 < score < 1.0

    def test_parse_from_json(self):
        json_str = (
            '{"task":"Add feature",'
            '"subtasks":[{"task":"Step 1","subtasks":[]}]}'
        )
        tree = TreeSimilarity.parse(json_str)
        assert tree["task"] == "Add feature"
        assert len(tree["subtasks"]) == 1
