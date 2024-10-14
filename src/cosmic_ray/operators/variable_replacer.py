"""Implementation of the variable-replacement operator."""

from random import randint

from parso.python.tree import ExprStmt, Leaf, Number

from .operator import Argument, Example, Operator


class VariableReplacer(Operator):
    """An operator that replaces usages of named variables."""

    def __init__(self, cause_variable, effect_variable=None):
        self.cause_variable = cause_variable
        self.effect_variable = effect_variable

    @classmethod
    def arguments(cls):
        return (
            Argument("cause_variable", "The cause variable"),
            Argument("effect_variable", "The effect variable"),
        )

    def mutation_positions(self, node):
        """Mutate usages of the specified cause variable. If an effect variable is also
        specified, then only mutate usages of the cause variable in definitions of the
        effect variable."""

        if isinstance(node, ExprStmt):
            # Confirm that name node is used on right hand side of the expression
            cause_variables = list(self._get_causes_from_expr_node(node))
            cause_variable_names = [cause_variable.value for cause_variable in cause_variables]
            if self.cause_variable in cause_variable_names:
                mutation_position = (node.start_pos, node.end_pos)

                # If an effect variable is specified, confirm that it appears on left hand
                # side of the expression
                if self.effect_variable:
                    effect_variable_names = [v.value for v in node.get_defined_names()]
                    if self.effect_variable in effect_variable_names:
                        yield mutation_position

                # If no effect variable is specified, any occurrence of the cause variable
                # on the right hand side of an expression can be mutated
                else:
                    yield mutation_position

    def mutate(self, node, index):
        """Replace cause variable with random constant."""
        assert isinstance(node, ExprStmt)
        # Find all occurrences of the cause node in the ExprStatement and replace with a random number
        rhs = node.get_rhs()
        new_rhs = self._replace_named_variable_in_expr(rhs, self.cause_variable)
        node.children[2] = new_rhs
        return node

    def _get_causes_from_expr_node(self, expr_node):
        rhs = expr_node.get_rhs().children
        return self._flatten_expr(rhs)

    def _flatten_expr(self, expr):
        for item in expr:
            # Convert PythonNode to list of its children
            try:
                item_to_flatten = item.children
            except AttributeError:
                item_to_flatten = item
            #
            try:
                yield from self._flatten_expr(item_to_flatten)
            except TypeError:
                yield item_to_flatten

    def _replace_named_variable_in_expr(self, node, variable_name):
        if isinstance(node, Leaf):
            if node.value == variable_name:
                return Number(start_pos=node.start_pos, value=str(randint(-100, 100)))
            else:
                return node

        updated_child_nodes = []
        for child_node in node.children:
            updated_child_nodes.append(self._replace_named_variable_in_expr(child_node, variable_name))
        node.children = updated_child_nodes
        return node

    @classmethod
    def examples(cls):
        return (
            Example("y = x + z", "y = 10 + z", operator_args={"cause_variable": "x"}),
            Example(
                "j = x + z\ny = x + z",
                "j = x + z\ny = -2 + z",
                operator_args={"cause_variable": "x", "effect_variable": "y"},
            ),
            Example(
                "j = x + z\ny = x + z",
                "j = 1 + z\ny = x + z",
                operator_args={"cause_variable": "x", "effect_variable": "j"},
            ),
            Example("y = 2*x + 10 + j + x**2", "y=2*10 + 10 + j + -4**2", operator_args={"cause_variable": "x"}),
        )
