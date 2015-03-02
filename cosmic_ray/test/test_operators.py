import ast
import copy
import unittest

from cosmic_ray.operators.number_replacer import NumberReplacer


class Linearizer(ast.NodeVisitor):
    def __init__(self):
        self.nodes = []

    def generic_visit(self, node):
        self.nodes.append(node)
        super().generic_visit(node)


def linearize_tree(node):
    l = Linearizer()
    l.visit(node)
    return l.nodes


class TestNumberReplacer(unittest.TestCase):
    def test_replacement_activated_replacer(self):
        node = ast.parse('x = 1')
        replacer = NumberReplacer(0)
        replacer.visit(node)
        self.assertTrue(replacer.activated)

    def test_remove_first(self):
        node = ast.parse('x = 1')
        mutant = NumberReplacer(0).visit(copy.deepcopy(node))

        orig_nodes = linearize_tree(node)
        mutant_nodes = linearize_tree(mutant)

        self.assertEqual(len(orig_nodes),
                         len(mutant_nodes))

        self.assertNotEqual(
            ast.dump(node),
            ast.dump(mutant))

    def test_non_replacement_does_not_activate_replacer(self):
        node = ast.parse('x = 1')
        replacer = NumberReplacer(1)
        replacer.visit(node)
        self.assertFalse(replacer.activated)

    def test_replacer_ignore_non_nth_sites(self):
        node = ast.parse('x = 1')

        self.assertEqual(
            ast.dump(node),
            ast.dump(NumberReplacer(1).visit(copy.deepcopy(node))))
