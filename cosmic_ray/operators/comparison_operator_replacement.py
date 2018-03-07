"""This module contains mutation operators which replace one
comparison operator with another.
"""

import ast

from ..util import build_mutations, compare_ast
from .operator import ReplacementOperatorMeta


_AST_OPERATORS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
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

    to_ops = set(to_op
                 for idx, to_op
                 in build_mutations([from_op],
                                    lambda _: _AST_OPERATORS))
    for to_op in to_ops:
        if from_op is ast.Eq and to_op is ast.Is:
            pass
        elif from_op is ast.NotEq and to_op is ast.IsNot:
            pass
        else:
            yield to_op


# Maps from-ops to to-ops when the RHS is `None`
_RHS_IS_NONE_OPS = {
    ast.Eq: [ast.IsNot],
    ast.NotEq: [ast.Is],
    ast.Is: [ast.IsNot],
    ast.IsNot: [ast.Is],
}

_RHS_IS_INTEGER_OPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def _rhs_is_none_ops(from_op):
    assert issubclass(from_op, ast.AST)
    return _RHS_IS_NONE_OPS.get(from_op, ())


def _rhs_is_integer_ops(from_op):
    assert issubclass(from_op, ast.AST)
    return _RHS_IS_INTEGER_OPS


def _comparison_rhs_is_none(node):
    "Determine if the node is a comparison with `None` on the RHS."
    return ((len(node.comparators) == 1)
            and
            (compare_ast(node.comparators[0], ast.NameConstant(None))))


def _comparison_rhs_is_integer(node):
    return ((len(node.comparators) == 1)
            and
            isinstance(node.comparators[0], ast.Num))


def _build_mutations(node):
    """Given a Compare node, produce the list of mutated operations.

    Depending on the details of the Compare node, different tactics
    may be used to generate the list of mutations, in order to avoid
    generating mutants which we know will be incompetent.

    Args:
        node: A Compare node.

    Returns:
        A sequence of (idx, to-op) tuples describing the mutations for `ops`.
        The idx is the index into the list of ops for the Compare node
        (A single Compare node can contain multiple operators in order to
        represent expressions like 5 <= x < 10).
    """
    assert isinstance(node, ast.Compare)
    ops = _find_to_ops(node)
    return build_mutations(map(type, node.ops), ops)


def _find_to_ops(node):
    """Iterable of possible operators the node could be mutated to.
    """
    if _comparison_rhs_is_none(node):
        ops = _rhs_is_none_ops
    elif _comparison_rhs_is_integer(node):
        ops = _rhs_is_integer_ops
    else:
        ops = _all_ops
    return ops


def _create_replace_comparison_operator(from_op, to_op):
    class ReplaceComparisonOperator(
            metaclass=ReplacementOperatorMeta,
            from_op=from_op,
            to_op=to_op):  # pylint: disable=abstract-method
        """An operator that modifies comparisons."""

        def _mutations(self, node):
            """List of all mutations for a node that this operator should perform.

            Returns a list of `(idx, to_op)` where `idx` is an index into
            `node.ops` and `to_op` is an operator node class.

            This limits mutations to those from `from_op` to `to_op`.
            """
            return [(idx, to_op)
                    for idx, to_op
                    in _build_mutations(node)
                    if isinstance(node.ops[idx], self.from_op)
                    if to_op is self.to_op]

        def visit_Compare(self, node):  # pylint: disable=missing-docstring
            muts = self._mutations(node)
            if muts:
                return self.visit_mutation_site(node, len(muts))

            return node

        def mutate(self, node, idx):
            op_idx, to_op = self._mutations(node)[idx]
            assert isinstance(node.ops[op_idx], self.from_op)
            node.ops[op_idx] = to_op()
            return node

    return ReplaceComparisonOperator


# Create the operator classes
_MUTATION_OPERATORS = tuple(
    _create_replace_comparison_operator(from_op, to_op)
    for from_op in _AST_OPERATORS
    for to_op in _all_ops(from_op))


# Add them to the module namespace
for op in _MUTATION_OPERATORS:
    globals()[op.__name__] = op


def operators():
    "Iterable of all comparison operator replacement mutation operators."
    return iter(_MUTATION_OPERATORS)
