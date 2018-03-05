"""Implementation of the unary-operator-replacement operator.
"""

import ast

from ..util import build_mutations
from .operator import ReplacementOperator


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


class ReplaceUnaryOperator(ReplacementOperator):  # pylint: disable=abstract-method
    """An operator that modifies unary operators.

    This is subclassed for each valid from/to unary operator pair, and each
    subclass provides `from_op` and `to_op` class-level attributes. Each of
    these is an `ast.Node` or `None`.
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


def _create_replace_unary_operator(from_op, to_op):
    """Create a ReplaceUnaryOperator subclasses that mutates `from_op` to `to_op`.
    """
    return type(
        'ReplaceUnaryOperator_{}_{}'.format(
            from_op.__name__,
            'None' if to_op is None else to_op.__name__),
        (ReplaceUnaryOperator,),
        {'from_op': property(lambda self: from_op),
         'to_op': property(lambda self: to_op)})


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
