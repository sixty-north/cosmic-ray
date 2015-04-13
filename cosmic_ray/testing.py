import abc
from collections import namedtuple
from enum import Enum
from itertools import chain
import unittest


class Outcome(Enum):
    SURVIVED = 'survived'
    KILLED = 'killed'
    INCOMPETENT = 'incompetent'


TestResult = namedtuple('TestResult',
                        ['outcome',
                         'results'])


class TestRunner(metaclass=abc.ABCMeta):
    """Specifies the interface for test runners in the system.

    There are many ways to run unit tests in Python, and each method
    supported by Cosmic Ray should be provided by a TestRunner
    implementation.
    """
    def __init__(self, test_dir):
        self._test_dir = test_dir

    @property
    def test_dir(self):
        return self._test_dir

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
        except Exception as e:
            return TestResult(Outcome.INCOMPETENT,
                              str(e))


class UnittestRunner(TestRunner):
    """Discover and run tests in `test_dir`.

    If the tests pass, this returns `(True, result)`, otherwise it
    returns `(False, result)`.

    Any exceptions thrown out of the test run are simply propagated
    out of this function.
    """

    def _run(self):
        suite = unittest.TestLoader().discover(self.test_dir)
        result = unittest.TestResult()
        suite.run(result)

        return (
            result.wasSuccessful(),
            [(str(r[0]), r[1])
             for r in chain(result.errors,
                            result.failures)])
