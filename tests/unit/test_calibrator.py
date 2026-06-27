"""Tests for scoring calibrator."""
from eval_framework.scoring.calibrator import Calibrator
from eval_framework.models import Dimension, JudgeScoreCard


class TestCalibrator:
    def test_perfect_agreement(self):
        """Identical scores should give perfect agreement."""
        judge = [
            JudgeScoreCard(dimension=Dimension.D1, score=4, reasoning=""),
            JudgeScoreCard(dimension=Dimension.D2, score=3, reasoning=""),
        ]
        human = [
            JudgeScoreCard(dimension=Dimension.D1, score=4, reasoning=""),
            JudgeScoreCard(dimension=Dimension.D2, score=3, reasoning=""),
        ]
        agreement = Calibrator.compute_agreement(judge, human)
        assert agreement["overall_exact_match_rate"] == 1.0
        assert agreement["overall_mean_difference"] == 0.0
        assert Calibrator.is_calibrated(agreement) is True

    def test_partial_agreement(self):
        """Mixed scores should give partial agreement."""
        judge = [
            JudgeScoreCard(dimension=Dimension.D1, score=4, reasoning=""),
            JudgeScoreCard(dimension=Dimension.D2, score=3, reasoning=""),
        ]
        human = [
            JudgeScoreCard(dimension=Dimension.D1, score=5, reasoning=""),
            JudgeScoreCard(dimension=Dimension.D2, score=3, reasoning=""),
        ]
        agreement = Calibrator.compute_agreement(judge, human)
        assert agreement["overall_exact_match_rate"] == 0.5
        assert agreement["overall_mean_difference"] == 0.5
        # mean diff 0.5 > 0.10, not calibrated
        assert Calibrator.is_calibrated(agreement) is False

    def test_empty_input(self):
        """Empty score lists should not error."""
        agreement = Calibrator.compute_agreement([], [])
        assert agreement["overall_exact_match_rate"] == 0.0
        assert agreement["overall_mean_difference"] == 0.0
