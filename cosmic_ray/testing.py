from collections import namedtuple
from enum import Enum
from itertools import chain
import sys
import unittest

import decorator


class Outcome(Enum):
    SURVIVED = 'survived'
    KILLED = 'killed'
    INCOMPETENT = 'incompetent'


TestResult = namedtuple('TestResult',
                        ['outcome',
                         'results'])


@decorator.decorator
def isolate_imports(f, *args, **kwargs):
    modules = dict(sys.modules)
    result = f(*args, **kwargs)

    dels = [m for m in sys.modules if m not in modules]
    for m in dels:
        del sys.modules[m]

    return result


@isolate_imports
def run_tests(test_dir):
    """Discover and run tests in `test_dir`.

    If the tests pass, this returns `(True, result)`, otherwise it
    returns `(False, result)`.
    """
    try:
        suite = unittest.TestLoader().discover(test_dir)
        result = unittest.TestResult()
        suite.run(result)

        return TestResult(
            Outcome.SURVIVED if result.wasSuccessful() else Outcome.KILLED,
            [(str(r[0]), r[1])
             for r in chain(result.errors,
                            result.failures)])
    except Exception as e:
        return TestResult(Outcome.INCOMPETENT, str(e))
