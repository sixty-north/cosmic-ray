"""Remove named arguments
Remove in function call, named arguments

Because in a lot of vase, named arguments represents options or fields.

The lost of an option or a field must imply application failure.

Examples:
    - subprocess.Popen call
    - ORM (like django models)
"""
from parso.python.tree import PythonNode, Operator as tree_Operator
from cosmic_ray.operators.operator import Operator
from cosmic_ray.operators.util import ASTQuery


class RemoveNamedArgument(Operator):
    def mutation_positions(self, node):
        if ASTQuery(node).match(PythonNode, type='arglist'):
            for child in node.children:
                if ASTQuery(child).match(PythonNode, type='argument'):
                    yield child.start_pos, child.end_pos, child

    def mutate(self, node, index):
        assert isinstance(node, PythonNode)
        count = 0
        for i, child in enumerate(node.children):
            if ASTQuery(child).match(PythonNode, type='argument'):
                if count == index:
                    try:
                        next_child = node.children[i + 1]
                        if ASTQuery(next_child).match(tree_Operator, value=','):
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
        )
