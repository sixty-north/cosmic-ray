import ast

from .operator import Operator


class NumberReplacer(Operator):
    """An operator that modifies numeric constants."""

    def visit_Num(self, node):  # noqa # pylint: disable=invalid-name
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Modify the numeric value on `node`."""
        new_node = ast.Num(n=node.n + 1)
        return new_node
