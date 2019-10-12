"Implementation of the no-op operator."

from .operator import Operator


class NoOp(Operator):
    """An operator that makes no changes.

    This is primarily for baselining and debugging. It behaves like any other operator, but it makes no changes.
    Obviously this means that, if your test suite passes on unmutated code, it will still pass after applying this
    operator. Use with care.
    """

    def mutation_positions(self, node):
        yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        return node

    @classmethod
    def examples(cls):
        return (
            ('@foo\ndef bar(): pass', '@foo\ndef bar(): pass'),
            ('def bar(): pass', 'def bar(): pass'),
            ('1 + 1', '1 + 1'),
        )
