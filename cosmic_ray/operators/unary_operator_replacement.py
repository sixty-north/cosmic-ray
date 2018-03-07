"""Implementation of the unary-operator-replacement operator.
"""

import ast

from ..util import build_mutations
from .operator import ReplacementOperatorMeta


# None indicates we want to delete the operator
_AST_OPERATORS = (ast.UAdd, ast.USub, ast.Invert, ast.Not)


def _to_ops(from_op):
    """The sequence of operators which `from_op` could be mutated to.
    """

    for to_op in _AST_OPERATORS + (None,):
        if to_op and from_op is ast.Not:
            # 'not' can only be removed but not replaced with
            # '+', '-' or '~' b/c that may lead to strange results
            pass
        elif from_op is ast.UAdd and to_op is None:
            # '+1' => '1' yields equivalent mutations
            pass
        else:
            yield to_op


def _create_replace_unary_operator(from_op, to_op):
    """Create a ReplaceUnaryOperator subclasses that mutates `from_op` to `to_op`.
    """
    class ReplaceUnaryOperator(
            metaclass=ReplacementOperatorMeta,
            from_op=from_op,
            to_op=to_op):  # pylint: disable=abstract-method
        """An operator that modifies unary operators.
        """

        def visit_UnaryOp(self, node):  # pylint: disable=invalid-name, missing-docstring
            if isinstance(node.op, self.from_op):
                return self.visit_mutation_site(node)
            return node

        def mutate(self, node, _):
            "Perform the `idx`th mutation on node."
            if self.to_op is None:
                return node.operand

            node.op = self.to_op()
            return node

    return ReplaceUnaryOperator


# Create the mutation operator classes
_MUTATION_OPERATORS = tuple(
    _create_replace_unary_operator(_AST_OPERATORS[idx], to_op)
    for idx, to_op in build_mutations(_AST_OPERATORS, _to_ops))


# Add the mutation operator classes to the module namespace.
for op in _MUTATION_OPERATORS:
    globals()[op.__name__] = op


def operators():
    "Iterable of all unary operator replacement mutation operators."
    return iter(_MUTATION_OPERATORS)
