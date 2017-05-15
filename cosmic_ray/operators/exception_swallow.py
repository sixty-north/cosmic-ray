import ast

from .operator import Operator


class ExceptionSwallow(Operator):

    """An operator that deleter exception handling."""

    def visit_ExceptHandler(self, node):  # noq
        """ No need to replace Pass with itself, it is not a mutant """
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            return node
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Remove the handler, create an empty one"""
        new_node = ast.ExceptHandler(type=node.type, name=node.name,
                                     body=[ast.Pass()])
        return new_node
