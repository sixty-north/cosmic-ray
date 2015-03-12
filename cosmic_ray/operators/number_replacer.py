import ast

from .operator import Operator


class NumberReplacer(Operator):
    """A NodeTransformer that replaces the n-th occurrence of a `Num` node
    with another `Num` node with a different numeric value.
    """

    def visit_Num(self, node):
        return self.visit_mutation_site(node)

    def mutate(self, node):
        return ast.Num(n=node.n + 1,
                       lineno=node.lineno,
                       col_offset=node.col_offset)

    def __repr__(self):
        return 'NumberReplacer(target={})'.format(
            self._target)
