"Implementation of a test-runner for pytest-based tests."

from io import StringIO

import pytest

from cosmic_ray.testing.test_runner import TestRunner, TestRunnerFailure
from cosmic_ray.util import redirect_stdout


class ResultCollector:
    "Pytest plugin that collects results for later analysis."
    def __init__(self):
        self.reports = []

    def pytest_runtest_logreport(self, report):
        "Collect logreports into a list."
        self.reports.append(report)


class PytestRunner(TestRunner):
    """A TestRunner using pytest.

    This treats `test_args` as a single string. It splits this string and
    passes the result to `pytest.main()`. The args are passed directly to that
    function, so see it's documentation for a description of how the arguments
    are used.

    """

    def _run(self):
        collector = ResultCollector()

        args = self.test_args
        if args:
            args = args.split()
        else:
            args = []

        with StringIO() as stdout:
            with redirect_stdout(stdout):
                exit_code = pytest.main(args, plugins=[collector])

            if exit_code == 0:
                return (True, ())

            if exit_code == 1:
                return (False, [(repr(r), r.longreprtext)
                                for r in collector.reports if r.failed])

            stdout.seek(0)
            output = stdout.read()
            raise TestRunnerFailure('pytest exited non-zero', exit_code, output)
