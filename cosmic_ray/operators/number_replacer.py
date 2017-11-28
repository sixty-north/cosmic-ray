"""Implementation of the NumberReplacer operator.
"""

import ast

from .operator import Operator


# Maps mutation count to number offsets
OFFSET_MAP = {
    0: 1,
    1: -1,
}


class NumberReplacer(Operator):
    """An operator that modifies numeric constants."""

    def visit_Num(self, node):  # noqa # pylint: disable=invalid-name
        "Visit a number node."
        return self.visit_mutation_site(node, len(OFFSET_MAP))

    def mutate(self, node, idx):
        """Modify the numeric value on `node`."""

        assert idx in OFFSET_MAP, 'received count with no associated offset'

        offset = OFFSET_MAP[idx]
        new_node = ast.Num(n=node.n + offset)
        return new_node
