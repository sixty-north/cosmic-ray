try:
    from contextlib import redirect_stdout
except ImportError:
    import sys
    # redirect_stdout was introduced in Python 3.4
    class _RedirectStream:
        """
            Copied from Python 3.5's implementation. See:
            https://github.com/python/cpython/commit/83935e76e35cf8d2fb9fe2599420f8adf421b884#diff-edbcdd20abc32f8b018deb2353ae925a
        """
        _stream = None

        def __init__(self, new_target):
            self._new_target = new_target
            # We use a list of old targets to make this CM re-entrant
            self._old_targets = []

        def __enter__(self):
            self._old_targets.append(getattr(sys, self._stream))
            setattr(sys, self._stream, self._new_target)
            return self._new_target

        def __exit__(self, exctype, excinst, exctb):
            setattr(sys, self._stream, self._old_targets.pop())


    class redirect_stdout(_RedirectStream):
        """Context manager for temporarily redirecting stdout to another file."""
        _stream = "stdout"


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


def get_line_number(node):
    """Try to get the line number for `node`.

    If no line number is available, this returns "<UNKNOWN>".
    """
    if hasattr(node, 'lineno'):
        return node.lineno
    else:
        return '<UNKNOWN>'
