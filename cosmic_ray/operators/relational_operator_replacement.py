import ast

from .operator import Operator


# Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn

class ReplaceEq(Operator):
    def visit_Eq(self, node):
        self.visit_mutation_site(node)

    def mutate(self, node):
        return ast.NotEq()
