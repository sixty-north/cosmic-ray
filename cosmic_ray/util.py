import datetime


def get_line_number(node):
    """Try to get the line number for `node`.

    If no line number is available, this returns "<UNKNOWN>".
    """
    if hasattr(node, 'lineno'):
        return node.lineno
    else:
        return '<UNKNOWN>'


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
