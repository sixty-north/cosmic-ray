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

    This treats `test_args` as a list of arguments to `pytest.main()`. The args
    are passed directly to that function, so see it's documentation for a
    description of how the arguments are used.

    """

    def _run(self):
        collector = ResultCollector()

        with open(os.devnull, 'w') as devnull, redirect_stdout(devnull):
            pytest.main(list(self.test_args),
                        plugins=[collector])

        return (
            all(r.passed for r in collector.reports),
            [repr(r) for r in collector.reports if r.failed])
