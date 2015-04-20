import ast

from .operator import Operator


class NumberReplacer(Operator):
    """A NodeTransformer that replaces a `Num` node with another `Num`
    node holding a different numeric value.
    """

    def visit_Num(self, node):  # noqa
        return self.visit_mutation_site(node)

    def mutate(self, node):
        new_node = ast.Num(n=node.n + 1)
        return new_node

    def __repr__(self):
        return 'NumberReplacer(target={})'.format(
            self._target)
