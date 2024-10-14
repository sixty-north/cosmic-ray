"""Implementation of the variable-inserter operator."""

import random

import parso.python.tree
from parso.python.tree import Name, PythonNode

from .operator import Argument, Example, Operator


class VariableInserter(Operator):
    """An operator that replaces usages of named variables to particular statements."""

    def __init__(self, cause_variable, effect_variable):
        self.cause_variable = cause_variable
        self.effect_variable = effect_variable

    @classmethod
    def arguments(cls):
        return (
            Argument("cause_variable", "The cause variable"),
            Argument("effect_variable", "The effect variable"),
        )

    def mutation_positions(self, node):
        """Find expressions or terms that define the effect variable. These nodes can be
        mutated to introduce an effect of the cause variable.
        """
        if isinstance(node, PythonNode) and (node.type == "arith_expr" or node.type == "term"):
            expr_node = node.search_ancestor("expr_stmt")
            if expr_node:
                effect_variable_names = [v.value for v in expr_node.get_defined_names()]
                if self.effect_variable in effect_variable_names:
                    cause_variables = list(self._get_causes_from_expr_node(expr_node))
                    if node not in cause_variables:
                        yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        """Join the node with cause variable using a randomly sampled arithmetic operator."""
        assert isinstance(node, PythonNode)
        assert node.type == "arith_expr" or node.type == "term"

        arith_operator = random.choice(["+", "*", "-"])
        arith_operator_node_start_pos = self._iterate_col(node.end_pos)
        cause_node_start_pos = self._iterate_col(arith_operator_node_start_pos)
        arith_operator_node = parso.python.tree.Operator(arith_operator, start_pos=arith_operator_node_start_pos)
        cause_node = Name(self.cause_variable, start_pos=cause_node_start_pos)
        replacement_node = parso.python.tree.PythonNode("arith_expr", [node, arith_operator_node, cause_node])
        return replacement_node

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

    @staticmethod
    def _iterate_col(position_tuple):
        return tuple(sum(x) for x in zip(position_tuple, (0, 1)))

    @classmethod
    def examples(cls):
        return (
            Example("y = x + z", "y = x + z * j", operator_args={"cause_variable": "j", "effect_variable": "y"}),
            Example(
                "j = x + z\ny = x + z",
                "j = x + z + x\ny = x + z",
                operator_args={"cause_variable": "x", "effect_variable": "j"},
            ),
        )
