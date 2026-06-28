"""Multi-language test execution and scoring."""

import dataclasses
import re
import subprocess
from abc import ABC, abstractmethod


@dataclasses.dataclass
class TestRunResult:
    score: float  # 0.0 to 1.0
    passed: int
    failed: int
    errors: int
    output: str
    pass_threshold: float = 0.85

    @property
    def passed_threshold(self) -> bool:
        return self.score >= self.pass_threshold


class LanguageTestRunner(ABC):
    def __init__(self, language: str):
        self.language = language

    def run(
        self,
        working_dir: str,
        test_command: str,
        pass_threshold: float = 0.85,
        timeout: int = 120,
    ) -> TestRunResult:
        """Run tests and parse the output into a score."""
        proc = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=working_dir,
            timeout=timeout,
        )
        return self._parse_output(
            proc.stdout + proc.stderr, pass_threshold
        )

    @abstractmethod
    def _parse_output(
        self, output: str, pass_threshold: float
    ) -> TestRunResult:
        ...


class PythonTestRunner(LanguageTestRunner):
    def __init__(self):
        super().__init__("python")

    def _parse_output(
        self, output: str, pass_threshold: float
    ) -> TestRunResult:
        passed = 0
        failed = 0
        errors = 0
        for line in output.split("\n"):
            if " passed" in line:
                m = re.search(r"(\d+)\s+passed", line)
                if m:
                    passed = int(m.group(1))
            if " failed" in line:
                m = re.search(r"(\d+)\s+failed", line)
                if m:
                    failed = int(m.group(1))
            if " error" in line and "errors" in line:
                m = re.search(r"(\d+)\s+error", line)
                if m:
                    errors = int(m.group(1))

        total = passed + failed + errors
        score = passed / total if total > 0 else 0.0
        return TestRunResult(
            score=score,
            passed=passed,
            failed=failed,
            errors=errors,
            output=output,
            pass_threshold=pass_threshold,
        )


class TestRunnerFactory:
    _runners = {
        "python": PythonTestRunner,
    }

    @classmethod
    def get(cls, language: str) -> LanguageTestRunner:
        if language not in cls._runners:
            raise ValueError(
                f"No test runner for '{language}'. "
                f"Available: {list(cls._runners.keys())}"
            )
        return cls._runners[language]()
