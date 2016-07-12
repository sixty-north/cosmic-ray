import abc
from collections import namedtuple
from enum import Enum
import sys
import traceback


class Outcome(Enum):
    """A enum of the possible outcomes for any mutant test run.
    """
    SURVIVED = 'survived'
    KILLED = 'killed'
    INCOMPETENT = 'incompetent'


# The type returned by TestRunner runs.
TestResult = namedtuple('TestResult',
                        ['outcome',
                         'results'])


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
        """The sequence of arguments for the test runner.
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
        raise NotImplemented()

    def __call__(self):
        """Call `_run()` and return a `TestResult` with the results.

        The `outcome` field of the return value is:

        - SURVIVED if the tests passed
        - KILLED if the tests failed
        - INCOMPETENT if the tests raised an exception.

        The `results` field is simply the second field of
        `test_runner.run()`'s return value.
        """
        try:
            test_result = self._run()
            if test_result[0]:
                return TestResult(Outcome.SURVIVED,
                                  test_result[1])
            else:
                return TestResult(Outcome.KILLED,
                                  test_result[1])
        except Exception:
            return TestResult(Outcome.INCOMPETENT,
                              traceback.format_exception(*sys.exc_info()))
