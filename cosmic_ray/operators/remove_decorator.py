import ast

from .operator import Operator


class RemoveDecorator(Operator):
    """An operator that removes each of the non standard decorators."""
    regular_decorators = ["classmethod", "staticmethod", "abstractmethod"]

    def visit_FunctionDef(self, node):  # noqa
        decorator_candidates = [x for x in node.decorator_list if \
                                x.id not in self.regular_decorators]
        if decorator_candidates:
            return self.visit_mutation_site(node, len(decorator_candidates))

        return node

    def mutate(self, node, idx):
        """Modify the decorator list to remove one decorator at each mutation"""
        decorator_candidates = [x for x in node.decorator_list if \
                                x.id not in self.regular_decorators]
        removed_decorator = decorator_candidates[idx]
        modified_decorator = [x for x in node.decorator_list if \
                              x.id != removed_decorator.id]
        node.decorator_list = modified_decorator
        
        return node
