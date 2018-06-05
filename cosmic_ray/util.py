"""Various utility functions with no better place to live.
"""
import ast
import enum
import itertools

try:
    from contextlib import redirect_stdout
except ImportError:

    import sys


    # noqa # redirect_stdout was introduced in Python 3.4
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


    # noqa # pylint: disable=invalid-name
    class redirect_stdout(_RedirectStream):  # noqa
        """Context manager for temporarily redirecting stdout to another
        file."""
        _stream = "stdout"

try:
    # pylint: disable=unused-import, ungrouped-imports
    from contextlib import redirect_stderr
except ImportError:
    # redirect_stderr was introduced in Python 3.5
    # pylint: disable=invalid-name
    class redirect_stderr(redirect_stdout):
        """
            Copied from Python 3.5's implementation. See:
            https://github.com/python/cpython/commit/83935e76e35cf8d2fb9fe2599420f8adf421b884#diff-edbcdd20abc32f8b018deb2353ae925a
        """

        _stream = "stderr"


def get_line_number(node):
    """Try to get the line number for `node`.

    If no line number is available, this returns -1.
    """
    try:
        return node.lineno
    except AttributeError:
        return -1


def get_col_offset(node):
    """Try to get the column offset for `node`.

    If no column offset is available, this returns -1.
    """
    try:
        return node.col_offset
    except AttributeError:
        return -1


def build_mutations(ops, to_ops):
    """The sequence of `(idx, to-op)` tuples describing the mutations for `ops`.

    Each `idx` is an index into `ops` indicating the operator to be mutated
    from. Each `to-op` is the operator class to be mutated to.

    This will never produce mutations from an operator to itself.

    If `to_ops` includes `None` in its output, that means to delete the
    from-operator.

    Args:
      ops: A sequence of AST operator classes
      to_ops: A unary callable which takes a from-operator class and returns an
        iterable of operator classes (or `None`) to mutate to.
    """
    return [(idx, to_op)
            for idx, from_op in enumerate(ops)
            for to_op in to_ops(from_op)
            if from_op is not to_op]


def compare_ast(node1, node2):
    """Compares two AST nodes for equality.

    Ignores the lineno, col_offset and ctx attributes.

    Args:
        node1: An AST node.
        node2: Another AST node.

    Returns:
        True if the nodes are equivalent, otherwise False.
    """
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue
            if not compare_ast(v, getattr(node2, k)):
                return False
        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(compare_ast, zip(node1, node2)))
    return node1 == node2


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def index_of_first_difference(*iterables):
    """The index of the first unequal elements in two iterable series.

    Args:
        *iterables: Iterable series.
    """
    for index, items in enumerate(zip(*iterables)):
        if not all_equal(items):
            return index
    raise IndexError("Iterables have equal contents.")

def all_equal(iterable):
    return all(a == b for a, b in pairwise(iterable))


class StrEnum(str, enum.Enum):
    pass
