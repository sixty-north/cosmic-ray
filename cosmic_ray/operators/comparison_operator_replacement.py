"""This module contains mutation operators which replace one
comparison operator with another.
"""

import ast

from .operator import Operator
from ..util import build_mutations

OPERATORS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
             ast.Is, ast.IsNot, ast.In, ast.NotIn)


def _to_ops(from_op):
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


class MutateComparisonOperator(Operator):
    """An operator that modifies comparisons."""

    def visit_Compare(self, node):  # pylint: disable=invalid-name
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#Compare
        """
        return self.visit_mutation_site(
            node,
            len(build_mutations(node.ops, _to_ops)))

    def mutate(self, node, idx):
        from_idx, to_op = build_mutations(node.ops, _to_ops)[idx]
        node.ops[from_idx] = to_op()
        return node
