"Implementation of the remove-decorator operator."

from parso.python.tree import Decorator

from .operator import Example, Operator


class RemoveDecorator(Operator):
    """An operator that removes decorators."""

    def mutation_positions(self, node):
        if isinstance(node, Decorator):
            yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert isinstance(node, Decorator)
        assert index == 0

    @classmethod
    def examples(cls):
        return (
            Example("@foo\ndef bar(): pass", "def bar(): pass"),
            Example("@first\n@second\ndef bar(): pass", "@second\ndef bar(): pass"),
            Example("@first\n@second\ndef bar(): pass", "@first\ndef bar(): pass", occurrence=1),
            Example("@first\n@second\n@third\ndef bar(): pass", "@first\n@third\ndef bar(): pass", occurrence=1),
        )
