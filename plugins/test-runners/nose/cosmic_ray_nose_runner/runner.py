"Implementation of test-runner for nose tests."

import os

import nose

from cosmic_ray.testing.test_runner import TestRunner
from cosmic_ray.util import redirect_stdout, redirect_stderr


class NoseResultsCollector(nose.plugins.Plugin):
    "Nose plugin that collects results for later analysis."
    name = 'cosmic_ray'
    enabled = True

    def __init__(self):
        super().__init__()
        self.result = None

    def finalize(self, result):
        "Store result."
        self.result = result


class NoseRunner(TestRunner):  # pylint: disable=too-few-public-methods
    """A TestRunner using nosetest.

    This treats `test_args` as a list of arguments to `nose.run()`. The args
    are passed directly to that function. See nose's command line reference
    for a description of what arguments are accepted.

    NOTE: ``-s`` is not accepted here!
    """

    def _run(self):
        argv = ['', '--with-cosmic_ray']
        argv += self.test_args.split()
        collector = NoseResultsCollector()

        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull):
                with redirect_stderr(devnull):
                    nose.run(argv=argv, plugins=[collector])
        return (collector.result.wasSuccessful(),
                [r[1] for r in collector.result.errors +
                 collector.result.failures])
