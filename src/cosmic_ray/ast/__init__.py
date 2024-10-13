"Tools for working with parso ASTs."

import io
from abc import ABC, abstractmethod
from pathlib import Path

import parso.python.tree
import parso.tree

from cosmic_ray.util import read_python_source


class Visitor(ABC):
    """AST visitor for parso trees.

    This supports both simple traversal as well as editing of the tree.
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
        """Called for each node in the walk.

        This should return a node that will replace the node argument in the AST. This can be
        the node argument itself, a new node, or None. If None is returned, then the node is
        removed from the tree.

        Args:
            node: The node currently being visited.

        Returns:
            A node or `None`.
        """


def ast_nodes(node):
    """Iterable of all nodes in a tree.

    Args:
        node: The top node in a parso tree to iterate.

    Yields:
        All of the nodes in the tree.
    """
    yield node

    if isinstance(node, parso.tree.BaseNode):
        for child in node.children:
            yield from ast_nodes(child)


def get_ast_from_path(module_path: Path):
    """Get the AST for the code in a file.

    Args:
        module_path: pathlib.Path to the file containing the code.

    Returns:
        The parso parse tree for the code in `module_path`.
    """
    source = read_python_source(module_path)
    return get_ast(source)


def get_ast(source: str):
    """Parse the AST for a code string.

    Args:
        code (str): _description_
    """
    return parso.parse(source)


def is_none(node):
    "Determine if a node is the `None` keyword."
    return isinstance(node, parso.python.tree.Keyword) and node.value == "None"


def is_number(node):
    "Determine if a node is a number."
    return isinstance(node, parso.python.tree.Number)


def dump_node(node):
    "Generate string version of node."
    buffer = io.StringIO()
    write = buffer.write

    def do_dump(node, indent=""):
        write(f"{indent}{type(node).__name__}({node.type}")
        value = getattr(node, "value", None)
        if value:
            value = value.replace("\n", "\\n")
            write(f", '{value}'")
        children = getattr(node, "children", None)
        if children:
            write(", [\n")
            for child in children:
                do_dump(child, indent + " " * 4)
                write(",\n")
            write(f"{indent}]")
        write(")")
        if not indent:
            write("\n")

    do_dump(node)
    return buffer.getvalue()
