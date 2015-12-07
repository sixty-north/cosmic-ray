import ast

from .operator import Operator


class ReverseUnarySub(Operator):
    """A NodeTransformer that deletes unary subtraction (i.e. negation).
    """

    def visit_UnaryOp(self, node):  # noqa
        if isinstance(node.op, ast.USub):
            return self.visit_mutation_site(node)
        else:
            return node

    def mutate(self, node):
        """Replace the unary-sub operator with unary-add.
        """
        node.op = ast.UAdd()
        return node


class ReverseUnaryAdd(Operator):
    """A NodeTransformer that reverses unary addition (i.e. the positive sign).
    """

    def visit_UnaryOp(self, node):  # noqa
        if isinstance(node.op, ast.UAdd):
            return self.visit_mutation_site(node)
        else:
            return node

    def mutate(self, node):
        """Replace the unary-add operator with unary-sub.
        """
        node.op = ast.USub()
        return node
