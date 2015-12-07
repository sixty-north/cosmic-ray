"""This module contains mutation operators which replace one
relational operator with another.

For each relational operator we generate a series of classes, one for
each *other* operator. These generated classes mutate nodes by
replaces the first operator with the second.

The generated classes are named `Replace<from-op>With<to-op>` where
`from-op` is the relational operator being replaced and `to-op` is the
replacement operator.

The global list `operators` also contains a all of the generated
classes. This list is primarily used for testing.
"""

import ast

from .operator import Operator


RELATIONAL_OPERATORS = {ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                        ast.Is, ast.IsNot, ast.In, ast.NotIn}

# There are a number of potential replacements which we avoid because
# they almost always produce equivalent mutants. This is a set of
# (FROM-OP, TO-OP) tuples which we don't want to generate.
SKIP = {
    (ast.NotEq, ast.IsNot),
}


def _create_operator(from_op, to_op):  # pylint:disable=redefined-outer-name
    """Create an operator which replaces `from_op` with `to_op`.

    This inserts the class into the global namespace with the name
    `ReplaceXXXWithYYY'.

    Returns the new class
    """
    operator_name = 'Replace{}With{}'.format(
        from_op.__name__, to_op.__name__)

    visit_func_name = 'visit_{}'.format(from_op.__name__)
    visit_func = lambda self, node: self.visit_mutation_site(node)  # noqa

    new_op = type(
        operator_name,
        (Operator,),
        {'mutate': lambda self, node: to_op(),
         visit_func_name: visit_func,
         'from_op': from_op})

    globals()[operator_name] = new_op
    return new_op


# For each relational operator A, create one class for each *other*
# relational operator B which replaces A with B in an AST.
OPERATORS = [_create_operator(from_op, to_op)
             for from_op in RELATIONAL_OPERATORS
             for to_op in RELATIONAL_OPERATORS.difference({from_op})
             if (from_op, to_op) not in SKIP]
