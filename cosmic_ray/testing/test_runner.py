import abc
import sys
import traceback

from cosmic_ray.work_record import WorkRecord


class TestOutcome:  # pylint: disable=too-few-public-methods
    """A enum of the possible outcomes for any mutant test run.
    """
    SURVIVED = 'survived'
    KILLED = 'killed'
    INCOMPETENT = 'incompetent'


# pylint: disable=too-few-public-methods
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
        """Call `_run()` and return a `WorkRecord` with the results.

        Returns: A `WorkRecord` with the `test_outcome` and `data` fields
            filled in.
        """
        try:
            test_result = self._run()
            if test_result[0]:
                return WorkRecord(
                    test_outcome=TestOutcome.SURVIVED,
                    data=test_result[1])
            return WorkRecord(
                test_outcome=TestOutcome.KILLED,
                data=test_result[1])
        except Exception:  # pylint: disable=broad-except
            return WorkRecord(
                test_outcome=TestOutcome.INCOMPETENT,
                data=traceback.format_exception(*sys.exc_info()))
