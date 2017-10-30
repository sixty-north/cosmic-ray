try:
    from contextlib import redirect_stdout
except ImportError:

    import sys


    # noqa # redirect_stdout was introduced in Python 3.4
    class _RedirectStream:  # pylint: disable=too-few-public-methods
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


    # noqa # pylint: disable=invalid-name,too-few-public-methods
    class redirect_stdout(_RedirectStream):  # noqa
        """Context manager for temporarily redirecting stdout to another
        file."""
        _stream = "stdout"

try:
    # pylint: disable=unused-import, ungrouped-imports
    from contextlib import redirect_stderr
except ImportError:
    # redirect_stderr was introduced in Python 3.5
    # pylint: disable=invalid-name,too-few-public-methods
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
    return '<UNKNOWN>'


def build_mutations(ops, to_ops):
    """The sequence of `(idx, to-op)` tuples describing the mutations for `ops`.

    Each `idx` is an index into `ops` indicating the operator to be mutated
    from. Each `to-op` is the operator class to be mutated to.

    @ops - a list of operations we want to mutate
    @to_ops - callable - yields all possible values to mutate to
    """
    # note: mutations to self are excluded.
    # None is a special mutation meaning to delete the operator!
    # 1) when to_op is None isinstance(from_op, None) will blow up because
    #    the second parameter needs to be a class
    # 2) when to_op != None we do the isinstance() check to figure out
    #    whether or not to include the operator in the list of possible
    #    mutations
    #
    # The `if to_op is None or isinstance(from_op, to_op)` expression handles
    # both scenarios very elegantly. First we handle 1) and if this is True
    # the rest of the expression is not evaluated and None is returned. Else
    # we're in scenario 2) where the left part of the expression is False so
    # the right part is evaluated. Since the left part of the expression has
    # confirmed that to_op != None then we're confident that the isinstance()
    # method will always work.
    return [(idx, to_op)
            for idx, from_op in enumerate(ops)
            for to_op in to_ops(from_op)
            if to_op is None or not isinstance(from_op, to_op)]
