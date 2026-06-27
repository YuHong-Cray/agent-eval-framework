"""Scoring calibration — compares LLM-Judge scores against human review."""

from eval_framework.models import JudgeScoreCard


class Calibrator:
    """Computes agreement between LLM-Judge and human reviewer scores."""

    @staticmethod
    def compute_agreement(
        judge_cards: list[JudgeScoreCard],
        human_cards: list[JudgeScoreCard],
    ) -> dict:
        """Calculate per-dimension and overall agreement metrics.

        Returns:
            {
              "overall_exact_match_rate": 0.75,
              "overall_mean_difference": 0.2,
              "per_dimension": {"D1": {"match_rate": 0.8, "mean_diff": 0.1}, ...}
            }
        """
        judge_map = {c.dimension.value: c for c in judge_cards}
        human_map = {c.dimension.value: c for c in human_cards}

        exact_matches = 0
        total_diff = 0.0
        per_dim = {}

        for dim in human_map:
            j = judge_map.get(dim)
            h = human_map[dim]
            if j:
                match = 1 if j.score == h.score else 0
                diff = abs(j.score - h.score)
                exact_matches += match
                total_diff += diff
                per_dim[dim] = {
                    "match_rate": match,
                    "mean_diff": diff,
                }

        n = len(per_dim) or 1
        return {
            "overall_exact_match_rate": exact_matches / n,
            "overall_mean_difference": total_diff / n,
            "per_dimension": per_dim,
        }

    @staticmethod
    def is_calibrated(agreement: dict, threshold: float = 0.10) -> bool:
        """Judge is considered calibrated if mean difference ≤ threshold."""
        return agreement["overall_mean_difference"] <= threshold
