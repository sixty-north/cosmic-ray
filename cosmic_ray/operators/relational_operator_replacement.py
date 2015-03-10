import ast

from .operator import Operator


RELATIONAL_OPERATORS = {ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                        ast.Is, ast.IsNot, ast.In, ast.NotIn}

# For each relational operator A, create one class for each *other*
# relational operator B which replaces A with B in an AST.

operators = []

for from_op in RELATIONAL_OPERATORS:
    for to_op in RELATIONAL_OPERATORS.difference({from_op}):
        operator_name = 'Replace{}With{}'.format(
            from_op.__name__, to_op.__name__)

        visit_func_name = 'visit_{}'.format(from_op.__name__)
        visit_func = lambda self, node: self.visit_mutation_site(node)

        operators.append(
            type(operator_name,
                 (Operator,),
                 {'mutate': lambda self, node: to_op(),
                  visit_func_name: visit_func,
                  'from_op': from_op,
                  '__repr__': lambda self: 'replace {} with {}'.format(
                      from_op.__name__, to_op.__name__)}))
