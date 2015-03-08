import ast

from .operator import Operator


# Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn

class ReplaceEq(Operator):
    def visit_Eq(self, node):
        return self.visit_mutation_site(node)

    def mutate(self, node):
        return ast.NotEq()


class ReplaceNotEq(Operator):
    def visit_NotEq(self, node):
        return self.visit_mutation_site(node)

    def mutate(self, node):
        return ast.Eq()
