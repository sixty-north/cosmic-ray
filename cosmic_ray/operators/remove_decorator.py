from .operator import Operator


class RemoveDecorator(Operator):
    """An operator that removes each of the non standard decorators."""
    REGULAR_DECORATORS = frozenset(["classmethod", "staticmethod",
                                    "abstractmethod"])

    @classmethod
    def _candidates(cls, node):
        """Get a list of indices into `node.decorator_list` of decorators of
        `node` which can be removed via mutation.
        """

        def skip(dec):
            return hasattr(dec, 'id') and dec.id in cls.REGULAR_DECORATORS

        return [i for (i, d) in enumerate(node.decorator_list)
                if not skip(d)]

    def visit_FunctionDef(self, node):  # noqa # pylint: disable=invalid-name
        decorator_candidates = self._candidates(node)

        if decorator_candidates:
            return self.visit_mutation_site(node, len(decorator_candidates))

        return node

    def mutate(self, node, idx):
        """Modify the decorator list to remove one decorator at each
         mutation"""
        candidates = self._candidates(node)
        del node.decorator_list[candidates[idx]]
        return node
