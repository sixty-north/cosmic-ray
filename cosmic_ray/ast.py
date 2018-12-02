"Tools for working with parso ASTs."

from abc import ABC, abstractmethod

import parso.python.tree
import parso.tree


class Visitor(ABC):
    """AST visitor for parso trees.
    """

    def walk(self, node):
        "Walk a parse tree, calling visit for each node."
        node = self.visit(node)

        if node is None:
            return None

        if isinstance(node, parso.tree.BaseNode):
            walked = map(self.walk, node.children)
            node.children = [child for child in walked if child is not None]

        return node

    @abstractmethod
    def visit(self, node):
        "Called for each node in the walk."


def get_ast(module_path, python_version):
    """Get the AST for the code in a file.

    Args:
        module_path: pathlib.Path to the file containing the code.
        python_version: Python version as a "MAJ.MIN" string.

    Returns: The parso parse tree for the code in `module_path`.
    """
    with module_path.open(mode='rt', encoding='utf-8') as handle:
        source = handle.read()

    return parso.parse(source, version=python_version)


def is_none(node):
    "Determine if a node is the `None` keyword."
    return isinstance(node, parso.python.tree.Keyword) and node.value == 'None'


def is_number(node):
    "Determine if a node is a number."
    return isinstance(node, parso.python.tree.Number)
