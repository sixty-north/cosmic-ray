from contextlib import redirect_stdout
try:
    from contextlib import redirect_stderr
except ImportError:
    # redirect_stderr was introduced in Python 3.5
    class redirect_stderr(redirect_stdout):
        """
            Copied from Python 3.5's implementation. See:
            https://github.com/python/cpython/commit/83935e76e35cf8d2fb9fe2599420f8adf421b884#diff-edbcdd20abc32f8b018deb2353ae925a
        """

        _stream = "stderr"

import nose
import os

from .test_runner import TestRunner


class NoseResultsCollector(nose.plugins.Plugin):
    name = 'cosmic_ray'
    enabled = True

    def __init__(self):
        super(self.__class__, self).__init__()
        self.result = None

    def finalize(self, result):
        self.result = result

class NoseRunner(TestRunner):
    """A TestRunner using nosetest.

    This treats `test_args` as a list of arguments to `nose.run()`. The args
    are passed directly to that function. See nose's command line reference
    for a description of what arguments are accepted.

    NOTE: ``-s`` is not accepted here!
    """

    def _run(self):
        argv = ['', '--with-cosmic_ray']
        argv += list(self.test_args)
        collector = NoseResultsCollector()

        with open(os.devnull, 'w') as devnull, \
            redirect_stdout(devnull), redirect_stderr(devnull):
            nose.run(argv=argv, plugins=[collector])
        return (collector.result.wasSuccessful(),
            [r[1] for r in collector.result.errors + collector.result.failures])
