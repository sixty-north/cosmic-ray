"Common implementation for operators that replace keywords."

from parso.python.tree import Keyword

from .operator import Operator

# pylint: disable=E1101


class KeywordReplacementOperator(Operator):
    """A base class for operators that replace one keyword with another
    """

    def mutation_positions(self, node):
        if isinstance(node, Keyword):
            if node.value.strip() == self.from_keyword:
                yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert isinstance(node, Keyword)
        assert node.value == self.from_keyword

        node.value = self.to_keyword
        return node

    @classmethod
    def examples(cls):
        return (
            (cls.from_keyword, cls.to_keyword),
        )
