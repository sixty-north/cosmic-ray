import ast
import sys
from .operator import Operator


class ReplaceTrueFalse(Operator):
    """An operator that modifies True/False constants."""
    def visit_NameConstant(self, node):  # noqa
        """
            New in version 3.4: Previously, these constants were instances of ``Name``.
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#NameConstant
        """
        if node.value in [True, False]:
            return self.visit_mutation_site(node)
        else:
            return node

    def visit_Name(self, node):  #noqa
        """For backward compatibility with Python 3.3."""
        if node.id in ['True', 'False']:
            return self.visit_mutation_site(node)
        else:
            return node

    def mutate(self, node):
        """Modify the boolean value on `node`."""
        if sys.version_info >= (3, 4):
            return ast.NameConstant(value=not node.value)
        else:
            return ast.Name(id=not ast.literal_eval(node.id), ctx=node.ctx)
