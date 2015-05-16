import ast

from .operator import Operator


class ReplaceBreakWithContinue(Operator):
    def visit_Break(self, node):
        return self.visit_mutation_site(node)

    def mutate(self, node):
        """Replace a Break node with a Continue node
        """
        assert isinstance(node, ast.Break)
        return ast.Continue()

    def __repr__(self):
        return 'ReplaceBreakWithContinue(target={})'.format(
            self._target)
