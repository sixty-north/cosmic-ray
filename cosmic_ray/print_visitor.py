import ast


class PrintVisitor(ast.NodeVisitor):
    """A `NodeVisitor` which simply prints information about the nodes it
    visits.
    """

    def __init__(self):
        self.indent = ''

    def generic_visit(self, node):
        """Print `node` and manage an indentation state."""
        print(self.indent, repr(node))
        self.indent += '    '
        super().generic_visit(node)  # pylint:disable=missing-super-argument
        self.indent = self.indent[:-4]

    def visit_Num(self,  # noqa # pylint:disable=invalid-name,no-self-use
                  node):
        print('a number:', node)


def dump_mod():
    import mod  # pylint:disable=import-error
    with open(mod.__file__, 'rt') as module_file:
        nodes = ast.parse(module_file.read())
    PrintVisitor().visit(nodes)
