"Implementation of the boolean replacement operators."

import ast
import sys

from .operator import Operator


class ReplaceTrueFalse(Operator):
    """An operator that modifies True/False constants."""

    def visit_NameConstant(self, node):  # noqa # pylint: disable=invalid-name
        """New in version 3.4: Previously, these constants were instances of
        ``Name``:
        http://greentreesnakes.readthedocs.io/en/latest/nodes.html#NameConstant
        """
        if node.value in [True, False]:
            return self.visit_mutation_site(node)
        return node

    def visit_Name(self, node):  # noqa # pylint: disable=invalid-name
        """For backward compatibility with Python 3.3."""
        if node.id in ['True', 'False']:
            return self.visit_mutation_site(node)
        return node

    def mutate(self, node, _):
        """Modify the boolean value on `node`."""
        if sys.version_info >= (3, 4):
            return ast.NameConstant(value=not node.value)
        return ast.Name(id=not ast.literal_eval(node.id), ctx=node.ctx)


class ReplaceAndWithOr(Operator):
    """An operator that swaps 'and' with 'or'."""

    def visit_BoolOp(self, node):  # noqa # pylint: disable=invalid-name
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#BoolOp
        """
        if isinstance(node.op, ast.And):
            return self.visit_mutation_site(node, len(node.values))
        return node

    def mutate(self, node, idx):
        """Replace AND with OR."""
        # replace all occurences of And()
        # A and B and C -> A or B or C
        node.op = ast.Or()

        # or replace an operator somewhere in the middle
        # of the expression
        if idx and len(node.values) > 2:
            left = node.values[:idx]
            if len(left) > 1:
                left = [ast.BoolOp(op=ast.And(), values=left)]

            right = node.values[idx:]
            if len(right) > 1:
                right = [ast.BoolOp(op=ast.And(), values=right)]

            node.values = []
            node.values.extend(left)
            node.values.extend(right)

        return node


class ReplaceOrWithAnd(Operator):
    """An operator that swaps 'or' with 'and'."""

    def visit_BoolOp(self, node):  # noqa # pylint: disable=invalid-name
        """
            http://greentreesnakes.readthedocs.io/en/latest/nodes.html#BoolOp
        """
        if isinstance(node.op, ast.Or):
            return self.visit_mutation_site(node, len(node.values))
        return node

    def mutate(self, node, idx):
        """Replace OR with AND."""
        if idx and len(node.values) > 2:
            left_list = node.values[:idx - 1]
            right_list = node.values[idx + 1:]
            left = node.values[idx - 1]
            right = node.values[idx]

            new_node = ast.BoolOp(op=ast.And(), values=[left, right])

            node.values = []
            node.values.extend(left_list)
            node.values.append(new_node)
            node.values.extend(right_list)
        else:
            node.op = ast.And()

        return node


class AddNot(Operator):
    """
        An operator that adds the 'not' keyword to boolean expressions.

        NOTE: 'not' as unary operator is mutated in
         `unary_operator_replacement.py`, including deletion of the same
         operator.
    """

    def visit_If(self, node):  # noqa # pylint: disable=invalid-name
        "Visit an 'if' node."
        return self.visit_mutation_site(node)

    def visit_IfExp(self, node):  # noqa # pylint: disable=invalid-name
        "Visit an 'if' expression node."
        return self.visit_mutation_site(node)

    def visit_Assert(self, node):  # noqa # pylint: disable=invalid-name
        "Visit an 'assert' node."
        return self.visit_mutation_site(node)

    def visit_While(self, node):  # noqa # pylint: disable=invalid-name
        "Visit a 'while' node."
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """
        Add the 'not' keyword.

        Note: this will negate the entire if condition.
        """
        if hasattr(node, 'test'):
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            return node
