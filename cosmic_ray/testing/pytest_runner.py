from contextlib import redirect_stdout
import os

import pytest

from .test_runner import TestRunner


class ResultCollector:
    def __init__(self):
        self.reports = []

    def pytest_runtest_logreport(self, report):
        self.reports.append(report)


class PytestRunner(TestRunner):
    """A TestRunner using py.test.

    This discovers all tests under `test_dir` and executes them.
    """

    def _run(self):
        collector = ResultCollector()

        with open(os.devnull, 'w') as devnull, redirect_stdout(devnull):
            pytest.main(['-x', self.test_dir],
                        plugins=[collector])

        return (
            all(r.passed for r in collector.reports),
            [repr(r) for r in collector.reports if r.failed])
