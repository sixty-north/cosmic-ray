import ast
import random

from .operator import Operator


class RemoveDecorator(Operator):
    """An operator that removes a single random decorator."""
    regular_decorators = ["classmethod", "staticmethod", "abstractmethod"]

    def visit_FunctionDef(self, node):  # noqa
        if [x for x in node.decorator_list if x.id not in self.regular_decorators]:
            return self.visit_mutation_site(node)
        return node

    def mutate(self, node, _):
        """Modify the decorator list to include randomly one less"""
        decorator_candidates = [x for x in node.decorator_list if x.id not in self.regular_decorators]
        removed_decorator = random.choice(decorator_candidates)
        modified_decorator = [x for x in node.decorator_list if x.id != removed_decorator.id]
        node.decorator_list = modified_decorator
        
        return node
