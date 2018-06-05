"Base test-runner implementation details."

import abc
import sys
import traceback

from cosmic_ray.util import StrEnum
from cosmic_ray.work_item import WorkItem


class TestOutcome(StrEnum):
    """A enum of the possible outcomes for any mutant test run.
    """
    SURVIVED = 'survived'
    KILLED = 'killed'
    INCOMPETENT = 'incompetent'


class TestRunnerFailure(Exception):
    """Failure reported from a test runner.
    """
    def __init__(self, msg, exit_code=None, output=None):  # pylint: disable=useless-super-delegation
        super().__init__(msg, exit_code, output)

    @property
    def msg(self):
        "A message describing the failure."
        return self.args[0]

    @property
    def exit_code(self):
        "The exit code of the test runner (if applicable)."
        return self.args[1]

    @property
    def output(self):
        "The output of the test runner (if applicable)."
        return self.args[2]


class TestRunner(metaclass=abc.ABCMeta):
    """Specifies the interface for test runners in the system.

    There are many ways to run unit tests in Python, and each method
    supported by Cosmic Ray should be provided by a TestRunner
    implementation.
    """

    def __init__(self, test_args):
        self._test_args = test_args

    @property
    def test_args(self):
        """The arguments for the test runner.

        This is typically just a string, but it's whatever was passed to the
        `TestRunner` initializer.
        """
        return self._test_args

    @abc.abstractmethod
    def _run(self):
        """Run all of the tests and return the results.

        The results are returned as a (success, result)
        tuple. `success` is a boolean indicating if the tests
        passed. `result` is any object that is appropriate to provide
        more information about the success/failure of the tests.
        """
        pass

    def __call__(self):
        """Call `_run()` and return a `WorkItem` with the results.

        Returns: A `WorkItem` with the `test_outcome` and `data` fields
            filled in.
        """
        try:
            test_result = self._run()
            if test_result[0]:
                return WorkItem(
                    test_outcome=TestOutcome.SURVIVED,
                    data=test_result[1])
            return WorkItem(
                test_outcome=TestOutcome.KILLED,
                data=test_result[1])
        except Exception:  # pylint: disable=broad-except
            return WorkItem(
                test_outcome=TestOutcome.INCOMPETENT,
                data=traceback.format_exception(*sys.exc_info()))
