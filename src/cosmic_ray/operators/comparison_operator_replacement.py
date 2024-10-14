"""This module contains mutation operators which replace one
comparison operator with another.
"""

import itertools
from enum import Enum

import parso.python.tree

from ..ast import is_none, is_number
from .operator import Example, Operator
from .util import extend_name


class ComparisonOperators(Enum):
    "All comparison operators that we mutate."

    Eq = "=="
    NotEq = "!="
    Lt = "<"
    LtE = "<="
    Gt = ">"
    GtE = ">="
    Is = "is"
    IsNot = "is not"


def _create_operator(from_op, to_op):
    @extend_name(f"_{from_op.name}_{to_op.name}")
    class ReplaceComparisonOperator(Operator):
        f"An operator that replaces {from_op.name} with {to_op.name}"

        def mutation_positions(self, node):
            if node.type == "comparison":
                # Every other child starting at 1 is a comparison operator of some sort
                for _, comparison_op in self._mutation_points(node):
                    yield (comparison_op.start_pos, comparison_op.end_pos)

        def mutate(self, node, index):
            points = list(itertools.islice(self._mutation_points(node), index, index + 1))
            assert len(points) == 1
            op_idx, _ = points[0]
            mutated_comparison_op = parso.parse(" " + to_op.value)
            node.children[op_idx * 2 + 1] = mutated_comparison_op
            return node

        @staticmethod
        def _mutation_points(node):
            for op_idx, comparison_op in enumerate(node.children[1::2]):
                if comparison_op.get_code().strip() == from_op.value:
                    rhs = node.children[(op_idx + 1) * 2]
                    if _allowed(to_op, from_op, rhs):
                        yield op_idx, comparison_op

        @classmethod
        def examples(cls):
            return (Example(f"x {from_op.value} y", f"x {to_op.value} y"),)

    return ReplaceComparisonOperator


# Build all of the binary replacement operators
_OPERATORS = tuple(
    _create_operator(from_op, to_op) for from_op, to_op in itertools.permutations(ComparisonOperators, 2)
)

# Inject the operators into the module namespace
for op_cls in _OPERATORS:
    globals()[op_cls.__name__] = op_cls


def operators():
    "Iterable of all binary operator replacement mutation operators."
    return iter(_OPERATORS)


# This determines the allowed from-to mutations when the RHS is None.
_RHS_IS_NONE_OPS = {
    ComparisonOperators.Eq: [ComparisonOperators.IsNot],
    ComparisonOperators.NotEq: [ComparisonOperators.Is],
    ComparisonOperators.Is: [ComparisonOperators.IsNot],
    ComparisonOperators.IsNot: [ComparisonOperators.Is],
}

# This determines the allowed to mutations when the RHS is a number
_RHS_IS_INTEGER_OPS = set(
    [
        ComparisonOperators.Eq,
        ComparisonOperators.NotEq,
        ComparisonOperators.Lt,
        ComparisonOperators.LtE,
        ComparisonOperators.Gt,
        ComparisonOperators.GtE,
    ]
)


def _allowed(to_op, from_op, rhs):
    "Determine if a mutation from `from_op` to `to_op` is allowed given a particular `rhs` node."
    if is_none(rhs):
        return to_op in _RHS_IS_NONE_OPS.get(from_op, ())

    if is_number(rhs):
        return to_op in _RHS_IS_INTEGER_OPS

    return True
