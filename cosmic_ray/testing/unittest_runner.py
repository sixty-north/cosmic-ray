from itertools import chain
import unittest

from .test_runner import TestRunner


class UnittestRunner(TestRunner):  # pylint:disable=no-init, too-few-public-methods
    """A TestRunner using `unittest`'s discovery mechanisms.

    This treats the first element of `test_args` as a directory. This discovers
    all tests under that directory and executes them.

    All elements in `test_args` after the first are ignored.

    """

    def _run(self):
        suite = unittest.TestLoader().discover(self.test_args[0])
        result = unittest.TestResult()
        result.failfast = True
        suite.run(result)

        return (
            result.wasSuccessful(),
            [r[1] for r in chain(result.errors, result.failures)])
