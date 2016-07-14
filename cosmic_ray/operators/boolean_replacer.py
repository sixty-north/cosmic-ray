import ast

from .operator import Operator


class BooleanReplacer(Operator):
    """An operator that modifies True/False constants.
    """
    def visit_NameConstant(self, node):  # noqa
        """
            New in version 3.4: Previously, these constants were instances of ``Name``.
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#NameConstant
        """
        if node.value in [True, False]:
            return self.visit_mutation_site(node)
        else:
            return node

    def mutate(self, node):
        """Modify the boolean value on `node`.
        """
        new_node = ast.NameConstant(value=not node.value)
        return new_node

