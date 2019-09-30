"""Remove named arguments
Remove in function call, named arguments

Because in a lot of vase, named arguments represents options or fields.

The lost of an option or a field must imply application failure.

Examples:
    - subprocess.Popen call
    - ORM (like django models)
"""
import re
from parso.python.tree import PythonNode, Operator as tree_Operator, Newline
from cosmic_ray.operators.operator import Operator
from cosmic_ray.operators.util import ObjTest


class RemoveNamedArguments(Operator):
    re_skip = re.compile(r'.*pragma:.*mutation-no-remove.*')

    def mutation_positions(self, node):
        if ObjTest(node).match(PythonNode, type='arglist'):
            for child in node.children:
                if ObjTest(child).match(PythonNode, type='argument'):
                    if not self._do_skip_argument(child):
                        yield child.start_pos, child.end_pos

    @classmethod
    def _do_skip_argument(cls, node):
        # Now we look if there is no # pragma: no-remove on any prefix
        # before the next newline
        t = ObjTest(node)
        while t and not t.match(Newline):
            t = t.get_next_leaf()
            prefix = t.prefix.obj
            if prefix:
                return cls.re_skip.match(prefix)
        return False

    def mutate(self, node, index):
        assert isinstance(node, PythonNode)
        count = 0
        for i, child in enumerate(node.children):
            if ObjTest(child).match(PythonNode, type='argument'):
                if not self._do_skip_argument(child):
                    if count == index:
                        try:
                            next_child = node.children[i + 1]
                            if ObjTest(next_child).match(tree_Operator, value=','):
                                del node.children[i + 1]
                        except IndexError:
                            pass
                        del node.children[i]
                        return node
                    count += 1

    @classmethod
    def examples(cls):
        return (
            ("f(1, b=2)", "f(1,)"),  # Ending coma is acceptable
            ("f(1, b=2, c=3)", "f(1, c=3)", 0),
            ("f(1, b=2, c=3)", "f(1, b=2,)", 1),

            ("f(a=1, b=2)", "f( b=2)", 0),
            ("f(a=1, b=2)", "f(a=1,)", 1),

            ("f(a=1, # pragma: mutation-no-remove\n  b=2)", "f(a=1,)", 0),
        )
