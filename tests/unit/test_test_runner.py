"""Tests for test_runner."""
import pytest

from eval_framework.scoring.test_runner import (
    LanguageTestRunner,
    TestRunnerFactory,
    TestRunResult,
)


class TestTestRunnerFactory:
    def test_get_python_runner(self):
        runner = TestRunnerFactory.get("python")
        assert isinstance(runner, LanguageTestRunner)
        assert runner.language == "python"

    def test_unsupported_language_raises(self):
        with pytest.raises(ValueError):
            TestRunnerFactory.get("rust")


class TestPythonTestRunner:
    def test_all_pass(self, tmp_path):
        """All tests passing should return score 1.0."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
def test_pass_1():
    assert 1 + 1 == 2

def test_pass_2():
    assert "hello".upper() == "HELLO"
"""
        )
        runner = TestRunnerFactory.get("python")
        result = runner.run(
            working_dir=str(tmp_path),
            test_command=f"pytest {test_file.name} -v",
        )
        assert result.score == 1.0
        assert result.passed >= 2
        assert result.failed == 0

    def test_partial_fail(self, tmp_path):
        """Some tests failing should return proportional score."""
        test_file = tmp_path / "test_mixed.py"
        test_file.write_text(
            """
def test_pass():
    assert True

def test_fail():
    assert False, "intentional failure"
"""
        )
        runner = TestRunnerFactory.get("python")
        result = runner.run(
            working_dir=str(tmp_path),
            test_command=f"pytest {test_file.name} -v",
        )
        assert result.score == 0.5
        assert result.passed == 1
        assert result.failed == 1
