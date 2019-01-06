"""Implementation of the NumberReplacer operator.
"""

import parso

from ..ast import is_number
from .operator import Operator

# List of offsets that we apply to numbers in the AST. Each index into the list
# corresponds to single mutation.
OFFSETS = [
    +1,
    -1,
]


class NumberReplacer(Operator):
    """An operator that modifies numeric constants."""

    def mutation_positions(self, node):
        if is_number(node):
            for _ in OFFSETS:
                yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        """Modify the numeric value on `node`."""

        assert index < len(OFFSETS), 'received count with no associated offset'
        assert isinstance(node, parso.python.tree.Number)

        val = eval(node.value) + OFFSETS[index]  # pylint: disable=W0123
        return parso.python.tree.Number(' ' + str(val), node.start_pos)

    @classmethod
    def examples(cls):
        return (
            ('x = 1', 'x = 2'),
            ('x = 1', 'x = 0', 1),
            ('x = 4.2', 'x = 5.2'),
            ('x = 4.2', 'x = 3.2', 1),
            ('x = 1j', 'x = (1+1j)'),
            ('x = 1j', 'x = (-1+1j)', 1),
        )
