from itertools import chain
import sys
import unittest

import decorator


@decorator.decorator
def isolate_imports(f, *args, **kwargs):
    modules = dict(sys.modules)
    try:
        return f(*args, **kwargs)
    finally:
        sys.modules = modules


# @isolate_imports
def run_tests(test_dir):
    """Discover and run tests in `test_dir`.

    If the tests pass, this returns `(True, result)`, otherwise it
    returns `(False, result)`.
    """
    suite = unittest.TestLoader().discover(test_dir)
    result = unittest.TestResult()
    suite.run(result)
    return (result.wasSuccessful(),
            [(str(r[0]), r[1])
             for r in chain(result.errors,
                            result.failures)])
