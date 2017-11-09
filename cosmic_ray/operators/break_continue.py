"""Implementation of the replace-break-with-continue and
replace-continue-with-break operators.
"""

import ast

from .operator import Operator


class ReplaceBreakWithContinue(Operator):
    "Operator which replaces 'break' with 'continue'."

    def visit_Break(self, node):  # pylint: disable=invalid-name
        "Visit a 'break' node."
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Replace a Break node with a Continue node."""
        assert isinstance(node, ast.Break)
        return ast.Continue()


class ReplaceContinueWithBreak(Operator):
    "Operator which replaces 'continue' with 'break'."

    def visit_Continue(self, node):  # pylint: disable=invalid-name
        "Visit a 'continue' node."
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Replace a Continue node with a Break node."""
        assert isinstance(node, ast.Continue)
        return ast.Break()
