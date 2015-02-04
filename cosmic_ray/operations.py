import ast
import copy
import itertools
import logging

log = logging.getLogger()


class ArithmeticOperatorDeletion(ast.NodeTransformer):
    """A NodeTransformer that deletes the n-th arithmetic operator.
    """
    def __init__(self, target):
        self._target = target
        self._count = 0
        self._activated = False

    @property
    def activated(self):
        "Whether this replace has performed any replacements."
        return self._activated

    def visit_Add(self, node):
        return self._visit_arithmetic_op(node)

    def visit_Sub(self, node):
        return self._visit_arithmetic_op(node)

    def visit_Mult(self, node):
        return self._visit_arithmetic_op(node)

    def visit_Div(self, node):
        return self._visit_arithmetic_op(node)

    def _visit_arithmetic_op(self, node):
        if self._count == self._target:
            self._activated = True
            log.info('ArithmeticOperatorDeletion: line number {}'.format(
                node.lineno))
            node = None

        self._count += 1
        return node

    def __repr__(self):
        return 'ArithmeticOperatorDeletion(target={})'.format(
            self._target)


def delete_arithmetic_operators(node):
    """Generate modified versions of `node` where arithmetic operators
    have been deleted.
    """
    for target in itertools.count():
        replacer = ArithmeticOperatorDeletion(target)
        clone = replacer.visit(copy.deepcopy(node))
        if not replacer.activated:
            break

        yield clone


class NumberReplacer(ast.NodeTransformer):
    """A NodeTransformer that replaces the n-th occurrence of a `Num` node
    with another `Num` node with a different numeric value.
    """
    def __init__(self, target):
        self._target = target
        self._count = 0
        self._activated = False

    @property
    def activated(self):
        "Whether this replace has performed any replacements."
        return self._activated

    def visit_Num(self, node):
        if self._count == self._target:
            self._activated = True
            log.info('NumberReplacer: line number {}'.format(
                node.lineno))
            node = ast.Num(n=node.n + 1)

        self._count += 1
        return node

    def __repr__(self):
        return 'NumberReplacer(target={})'.format(
            self._target)


def replace_constants(node):
    """Generate modified versions of `node` where constants have been
    replaced.
    """
    for target in itertools.count():
        replacer = NumberReplacer(target)
        clone = replacer.visit(copy.deepcopy(node))
        if not replacer.activated:
            break

        yield clone
