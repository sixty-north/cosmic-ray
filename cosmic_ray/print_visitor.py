import ast


class PrintVisitor(ast.NodeVisitor):
    def __init__(self):
        self.indent = ''

    def generic_visit(self, node):
        print(self.indent, repr(node))
        self.indent += '    '
        super().generic_visit(node)
        self.indent = self.indent[:-4]

    def visit_Num(self, node):
        import pdb; pdb.set_trace()
        print('a number:', node)


def dump_mod():
    import mod
    with open(mod.__file__, 'rt') as f:
        nodes = ast.parse(f.read())
    PrintVisitor().visit(nodes)
