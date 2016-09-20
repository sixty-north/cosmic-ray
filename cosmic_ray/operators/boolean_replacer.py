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

    def visit_Name(self, node):  # noqa
        """For backward compatibility with Python 3.3."""
        if node.id in ['True', 'False']:
            return self.visit_mutation_site(node)
        else:
            return node

    def mutate(self, node, _):
        """Modify the boolean value on `node`."""
        if sys.version_info >= (3, 4):
            return ast.NameConstant(value=not node.value)
        else:
            return ast.Name(id=not ast.literal_eval(node.id), ctx=node.ctx)


class ReplaceAndWithOr(Operator):
    """An operator that swaps 'and' with 'or'."""
    def visit_And(self, node):  # noqa
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#And
        """
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Replace AND with OR."""
        return ast.Or()


class ReplaceOrWithAnd(Operator):
    """An operator that swaps 'or' with 'and'."""
    def visit_Or(self, node):  # noqa
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#Or
        """
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Replace OR with AND."""
        return ast.And()


class RemoveNot(Operator):

    """An operator that removes the 'not' keyword from expressions."""

    def visit_UnaryOp(self, node):  # noqa
        """
        http://greentreesnakes.readthedocs.io/en/latest/nodes.html#UnaryOp
        """
        if isinstance(node.op, ast.Not):
            return self.visit_mutation_site(node)
        else:
            return node

    def mutate(self, node, _):
        """Remove the 'not' keyword."""
        # UnaryOp.operand is any expression node so just
        # return the expression without the 'not' keyword
        return node.operand


class AddNot(Operator):

    """An operator that adds the 'not' keyword to expressions."""

    def visit_If(self, node):  # noqa
        return self.visit_mutation_site(node)

    def visit_IfExp(self, node):  # noqa
        return self.visit_mutation_site(node)

    def visit_Assert(self, node):  # noqa
        return self.visit_mutation_site(node)

    def visit_While(self, node):  # noqa
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """
        Add the 'not' keyword.

        Note: this will negate the entire if condition.
        """
        if hasattr(node, 'test'):
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            # add lineno & col_offset to the nodes we created
            ast.fix_missing_locations(node)
            return node
