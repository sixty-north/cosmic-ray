"""This module contains mutation operators which replace one
comparison operator with another.
"""

import ast

from .operator import Operator
from ..util import build_mutations, compare_ast

OPERATORS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
             ast.Is, ast.IsNot, ast.In, ast.NotIn)


def _all_ops(from_op):
    """The sequence of operators which `from_op` could be mutated to.

    There are a number of potential replacements which we avoid because they
    almost always produce equivalent mutants. We encode those in the logic
    here.

    NB: This is an imperfect, stop-gap solution to the problem of certain
    equivalent mutants. Obviously `==` is not generally the same as `is`, but
    that mutation is also a source of a good number of equivalents. The real
    solution to this problem will probably come in the form of real exception
    declarations or something.

    See https://github.com/sixty-north/cosmic-ray/pull/162 for some more
    discussion of this issue.

    """

    for to_op in OPERATORS:
        if isinstance(from_op, ast.Eq) and to_op is ast.Is:
            pass
        elif isinstance(from_op, ast.NotEq) and to_op is ast.IsNot:
            pass
        else:
            yield to_op


_RHS_IS_NONE_OPS = {
    ast.Eq: [ast.IsNot],
    ast.NotEq: [ast.Is],
    ast.Is: [ast.IsNot],
    ast.IsNot: [ast.Is],
}


def _rhs_is_none_ops(from_op):
    for key, value in _RHS_IS_NONE_OPS.items():
        if isinstance(from_op, key):
            yield from value
            return


def _comparison_rhs_is_none(node):
    return ((len(node.comparators) == 1)
            and
            (compare_ast(node.comparators[0], ast.NameConstant(None))))


def _build_mutations(node):
    """Given a Compare node, produce the list of mutated operations.

    Depending on the details of the Compare node, different tactics
    may be used to generate the list of mutations, in order to avoid
    generating mutants which we know will be incompetent.

    Args:
        node: A Compare node.

    Returns:
        A sequence of (idx, to-op) tuples describing the mutations for `ops`.
    """
    assert isinstance(node, ast.Compare)
    if _comparison_rhs_is_none(node):
        ops = _rhs_is_none_ops
    else:
        ops = _all_ops
    return build_mutations(node.ops, ops)


class MutateComparisonOperator(Operator):
    """An operator that modifies comparisons."""

    def visit_Compare(self, node):
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#Compare
        """
        return self.visit_mutation_site(
            node,
            len(_build_mutations(node)))

    def mutate(self, node, idx):
        from_idx, to_op = _build_mutations(node)[idx]
        node.ops[from_idx] = to_op()
        return node
