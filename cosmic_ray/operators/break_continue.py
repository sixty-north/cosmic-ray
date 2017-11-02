import ast

from .operator import Operator


class ReplaceBreakWithContinue(Operator):
    def visit_Break(self, node):  # pylint: disable=invalid-name
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Replace a Break node with a Continue node."""
        assert isinstance(node, ast.Break)
        return ast.Continue()


class ReplaceContinueWithBreak(Operator):
    def visit_Continue(self, node):  # pylint: disable=invalid-name
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Replace a Continue node with a Break node."""
        assert isinstance(node, ast.Continue)
        return ast.Break()
