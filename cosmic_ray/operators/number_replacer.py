"""Implementation of the NumberReplacer operator.
"""

import ast

from .operator import Operator


# List of offsets that we apply to numbers in the AST. Each index into the list
# corresponds to single mutation.
OFFSETS = [
    +1,
    -1,
]


class NumberReplacer(Operator):
    """An operator that modifies numeric constants."""

    def visit_Num(self, node):  # noqa # pylint: disable=invalid-name
        "Visit a number node."
        return self.visit_mutation_site(node, len(OFFSETS))

    def mutate(self, node, idx):
        """Modify the numeric value on `node`."""

        assert idx < len(OFFSETS), 'received count with no associated offset'

        offset = OFFSETS[idx]
        new_node = ast.Num(n=node.n + offset)
        return new_node
