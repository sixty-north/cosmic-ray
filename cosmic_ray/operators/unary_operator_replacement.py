import ast

from .operator import Operator
from ..util import build_mutations

# None indicates we want to delete the operator
OPERATORS = (ast.UAdd, ast.USub, ast.Invert, ast.Not, None)


def _to_ops(from_op):
    """
        The sequence of operators which `from_op` could be mutated to.
    """

    for to_op in OPERATORS:
        if to_op and isinstance(from_op, ast.Not):
            # 'not' can only be removed but not replaced with
            # '+', '-' or '~' b/c that may lead to strange results
            pass
        elif isinstance(from_op, ast.UAdd) and (to_op is None):
            # '+1' => '1' yields equivalent mutations
            pass
        else:
            yield to_op


class MutateUnaryOperator(Operator):
    """An operator that modifies unary operators."""

    def visit_UnaryOp(self, node):  # pylint: disable=invalid-name
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#UnaryOp
        """
        return self.visit_mutation_site(
            node,
            len(build_mutations([node.op], _to_ops)))

    def mutate(self, node, idx):
        _, to_op = build_mutations([node.op], _to_ops)[idx]
        if to_op:
            node.op = to_op()
            return node
        return node.operand
