"""Implementation of the variable-replacement operator."""
from .operator import Operator
from parso.python.tree import Name, Number
from random import randint


class VariableReplacer(Operator):
    """An operator that replaces usages of named variables."""

    def __init__(self, cause_variable, effect_variable=None):
        self.cause_variable = cause_variable
        self.effect_variable = effect_variable

    def mutation_positions(self, node):
        """Mutate usages of the specified cause variable. If an effect variable is also
        specified, then only mutate usages of the cause variable in definitions of the
        effect variable."""

        if isinstance(node, Name) and node.value == self.cause_variable:

            # Confirm that name node is used on right hand side of the expression
            expr_node = node.search_ancestor('expr_stmt')
            if expr_node:
                cause_variables = expr_node.get_rhs().children
                if node in cause_variables:
                    mutation_position = (node.start_pos, node.end_pos)

                    # If an effect variable is specified, confirm that it appears on left hand
                    # side of the expression
                    if self.effect_variable:
                        effect_variable_names = [v.value for v in expr_node.get_defined_names()]
                        if self.effect_variable in effect_variable_names:
                            yield mutation_position

                    # If no effect variable is specified, any occurrence of the cause variable
                    # on the right hand side of an expression can be mutated
                    else:
                        yield mutation_position

    def mutate(self, node, index):
        """Replace cause variable with random constant."""
        assert isinstance(node, Name)

        return Number(start_pos=node.start_pos, value=str(randint(-100, 100)))

    @classmethod
    def examples(cls):
        return (
            # for cause_variable='x'
            ('y = x + z', 'y = 10 + z'),
            # for cause_variable='x' and effect_variable='y'
            ('j = x + z\ny = x + z', 'j = x + z\ny = -2 + z'),
            # for cause_variable='x' and effect_variable='j',
            ('j = x + z\ny = x + z', 'j = 1 + z\ny = -2 + z'),
            # for cause_variable='x'
            ('y = 2*x + 10 + j + x**2', 'y=2*10 + 10 + j + -4**2'),
        )
