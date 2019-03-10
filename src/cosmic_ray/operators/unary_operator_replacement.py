"""Implementation of the unary-operator-replacement operator.
"""

from enum import Enum
from itertools import permutations

from parso.python.tree import Keyword, Operator, PythonNode

from . import operator
from .util import extend_name


class UnaryOperators(Enum):
    "All unary operators that we mutate."
    UAdd = '+'
    USub = '-'
    Invert = '~'
    Not = 'not '
    Nothing = None


def _create_replace_unary_operators(from_op, to_op):
    if to_op.value is None:
        suffix = '_Delete_{}'.format(from_op.name)
    else:
        suffix = '_{}_{}'.format(from_op.name, to_op.name)

    @extend_name(suffix)
    class ReplaceUnaryOperator(operator.Operator):
        "An operator that replaces unary {} with unary {}.".format(
            from_op.name, to_op.name)

        def mutation_positions(self, node):
            if _is_unary_operator(node):
                op = node.children[0]
                if op.value.strip() == from_op.value.strip():
                    yield (op.start_pos, op.end_pos)

        def mutate(self, node, index):
            assert index == 0
            assert _is_unary_operator(node)

            if to_op.value is None:
                # This is a bit goofy since it can result in "return not x"
                # becoming "return  x" (i.e. with two spaces). But it's correct
                # enough.
                node.children[0].value = ''
            else:
                node.children[0].value = to_op.value
            return node

        @classmethod
        def examples(cls):
            from_code = '{}1'.format(from_op.value)
            to_code = from_code[len(from_op.value):]

            if to_op is not UnaryOperators.Nothing:
                to_code = to_op.value + to_code
            elif from_op is UnaryOperators.Not:
                to_code = ' ' + to_code

            return (
                (from_code, to_code),
            )

    return ReplaceUnaryOperator


def _is_factor(node):
    return (isinstance(node, PythonNode)
            and node.type in {'factor', 'not_test'} and len(node.children) > 0
            and isinstance(node.children[0], Operator))


def _is_not_test(node):
    return (isinstance(node, PythonNode) and node.type == 'not_test'
            and len(node.children) > 0
            and isinstance(node.children[0], Keyword)
            and node.children[0].value == 'not')


def _is_unary_operator(node):
    return _is_factor(node) or _is_not_test(node)


def _prohibited(from_op, to_op):
    "Determines if from_op is allowed to be mutated to to_op."
    # 'not' can only be removed but not replaced with
    # '+', '-' or '~' b/c that may lead to strange results
    if from_op is UnaryOperators.Not:
        if to_op is not UnaryOperators.Nothing:
            return True

    # '+1' => '1' yields equivalent mutations
    if from_op is UnaryOperators.UAdd:
        if to_op is UnaryOperators.Nothing:
            return True

    return False


_MUTATION_OPERATORS = tuple(
    _create_replace_unary_operators(from_op, to_op)
    for (from_op, to_op) in permutations(UnaryOperators, 2)
    if from_op.value is not None if not _prohibited(from_op, to_op))

for op_cls in _MUTATION_OPERATORS:
    globals()[op_cls.__name__] = op_cls


def operators():
    "Iterable of unary operator mutation operators."
    return _MUTATION_OPERATORS
