"Implementation of test-runner for nose2 tests."

import os

import traceback
import nose2

from cosmic_ray.testing.test_runner import TestRunner
from cosmic_ray.util import redirect_stdout, redirect_stderr


class Nose2ResultsCollector(object):
    "Nose plugin that collects results for later analysis."

    def __init__(self):
        self.events = []

    def testOutcome(self, event):  # pylint: disable=invalid-name
        "Store result."
        self.events.append(event)


class Nose2Runner(TestRunner):  # pylint: disable=too-few-public-methods
    """A TestRunner using nose2.

    This treats `test_args` as a list of arguments to `nose2.discover()`. The args
    are passed directly to that function. See nose2's command line reference
    for a description of what arguments are accepted.

    NOTE: ``-s`` is not accepted here!
    """

    def _run(self):
        argv = ['']
        argv += self.test_args.split()
        collector = Nose2ResultsCollector()

        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull):
                with redirect_stderr(devnull):
                    nose2.discover(argv=argv, extraHooks=[('testOutcome', collector)], exit=False)
        failures = [x for x in collector.events if x.outcome != 'passed']

        return (not failures, [(str(r.test), traceback.format_exception(*r.exc_info)) for r in failures])
