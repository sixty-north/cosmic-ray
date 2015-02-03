import ast
import copy
import itertools
import tempfile


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
            node = ast.Num(n=node.n + 1)

        self._count += 1
        return node


def test():
    code = '''
x = 0
    '''
    node = ast.parse(code)

    replace_constants(node)


def replace_constants(node):
    """Generate modified versions of node where constants have been
    replaced.
    """
    for target in itertools.count():
        replacer = NumberReplacer(target)
        clone = replacer.visit(copy.deepcopy(node))
        if not replace.activated:
            break

        yield clone


def replace_constant(node):
    pass
