"Implementation of the test-runner for `unittest`-based tests."

import unittest
from itertools import chain

from .test_runner import TestRunner


class UnittestRunner(TestRunner):
    """A TestRunner using `unittest`'s discovery mechanisms.

    This treats the `test_args` as a directory name. This discovers
    all tests under that directory and executes them.

    All elements in `test_args` after the first are ignored.

    """

    def _run(self):
        suite = unittest.TestLoader().discover(self.test_args)
        result = unittest.TestResult()
        result.failfast = True
        suite.run(result)

        return (
            result.wasSuccessful(),
            [r[1] for r in chain(result.errors, result.failures)])
