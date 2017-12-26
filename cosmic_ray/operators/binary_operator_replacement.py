"""Implementation of the binary-operator-replacement operator.
"""

import ast
import sys

from .operator import ReplacementOperatorMeta
from ..util import build_mutations

_AST_OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
                  ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor,
                  ast.BitAnd)

# todo: this often leads to unsupported syntax
if sys.version_info >= (3, 5):
    _AST_OPERATORS = _AST_OPERATORS + (ast.MatMult,)


def _to_ops(from_op):  # pylint: disable=unused-argument
    """The sequence of operators which `from_op` could be mutated to."""
    for to_op in _AST_OPERATORS:
        yield to_op


def _create_replace_binary_operator(from_op, to_op):
    class ReplaceBinaryOperator(
            metaclass=ReplacementOperatorMeta,
            from_op=from_op,
            to_op=to_op):
        """An operator that replaces binary operators."""
        def visit_BinOp(self, node):  # pylint: disable=invalid-name, missing-docstring
            if isinstance(node.op, self.from_op):
                return self.visit_mutation_site(node)
            return node

        def mutate(self, node, _):
            node.op = self.to_op()
            return node

    return ReplaceBinaryOperator


_MUTATION_OPERATORS = tuple(
    _create_replace_binary_operator(_AST_OPERATORS[idx], to_op)
    for idx, to_op in build_mutations(_AST_OPERATORS, _to_ops))


for op in _MUTATION_OPERATORS:
    globals()[op.__name__] = op


def operators():
    "Iterable of all binary operator replacement mutation operators."
    return iter(_MUTATION_OPERATORS)
