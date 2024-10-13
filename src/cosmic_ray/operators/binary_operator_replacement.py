"""Implementation of the binary-operator-replacement operator."""

import itertools
from enum import Enum

import parso

from .operator import Example, Operator
from .util import extend_name


class BinaryOperators(Enum):
    "All binary operators that we mutate."

    Add = "+"
    Sub = "-"
    Mul = "*"
    Div = "/"
    FloorDiv = "//"
    Mod = "%"
    Pow = "**"
    RShift = ">>"
    LShift = "<<"
    BitOr = "|"
    BitAnd = "&"
    BitXor = "^"


def _create_replace_binary_operator(from_op, to_op):
    @extend_name(f"_{from_op.name}_{to_op.name}")
    class ReplaceBinaryOperator(Operator):
        f"An operator that replaces binary {from_op.name} with binary {to_op.name}."

        def mutation_positions(self, node):
            if _is_binary_operator(node):
                if node.value == from_op.value:
                    yield (node.start_pos, node.end_pos)

        def mutate(self, node, index):
            assert _is_binary_operator(node)
            assert index == 0

            node.value = to_op.value
            return node

        @classmethod
        def examples(cls):
            return (Example(f"x {from_op.value} y", f"x {to_op.value} y"),)

    return ReplaceBinaryOperator


# Parent types of operators which indicate that the operator isn't binary.
_NON_BINARY_PARENTS = {
    "factor",  # unary operators, e.g. -1
    "argument",  # extended function definitions, e.g. def foo(*args)
    "star_expr",  # destructuring, e.g. a, *b = x
    "import_from",  # star import, e.g. from module import *
}


def _is_binary_operator(node):
    if isinstance(node, parso.python.tree.Operator):
        # This catches extended call syntax, e.g. call(*x)
        if isinstance(node.parent, parso.python.tree.Param):
            return False

        if node.parent.type in _NON_BINARY_PARENTS:
            return False

        return True

    return False


# Build all of the binary replacement operators
_MUTATION_OPERATORS = tuple(
    _create_replace_binary_operator(from_op, to_op) for from_op, to_op in itertools.permutations(BinaryOperators, 2)
)

# Inject operators into module namespace
for op_cls in _MUTATION_OPERATORS:
    globals()[op_cls.__name__] = op_cls


def operators():
    "Iterable of all binary operator replacement mutation operators."
    return _MUTATION_OPERATORS
