import ast
import copy
import itertools
import logging

log = logging.getLogger()


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
