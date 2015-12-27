"""Support for timing the execution of functions.

This is primarily intended to support baselining, but it's got some reasonable
generic functionality.
"""

import datetime
import subprocess


class Timer:
    """A simple context manager for timing events.

    Generally use it like this:

        with Timer() as t:
            do_something()
        print(t.elapsed())
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self._start = datetime.datetime.now()

    @property
    def elapsed(self):
        """Get the elapsed time between the last call to `reset` and now.

        Returns a `datetime.timedelta` object.
        """
        return datetime.datetime.now() - self._start

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        pass


def run_baseline(test_runner, module_name, test_dir):
    command = ('cosmic-ray',
               'baseline',
               '--test-runner={}'.format(test_runner),
               module_name,
               test_dir,)

    with Timer() as t:
        subprocess.run(command)

    return t.elapsed.total_seconds()
