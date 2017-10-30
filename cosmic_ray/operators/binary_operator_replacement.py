import ast
import sys

from .operator import Operator
from ..util import build_mutations

OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
             ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor,
             ast.BitAnd)

# todo: this often leads to unsupported syntax
if sys.version_info >= (3, 5):
    OPERATORS = OPERATORS + (ast.MatMult,)


def _to_ops(from_op):  # pylint: disable=unused-argument
    """The sequence of operators which `from_op` could be mutated to."""
    for to_op in OPERATORS:
        yield to_op


class MutateBinaryOperator(Operator):
    """An operator that modifies binary operators."""

    def visit_BinOp(self, node):  # pylint: disable=invalid-name
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#BinOp
        """
        return self.visit_mutation_site(
            node,
            len(build_mutations([node.op], _to_ops)))

    def mutate(self, node, idx):
        _, to_op = build_mutations([node.op], _to_ops)[idx]
        node.op = to_op()
        return node
