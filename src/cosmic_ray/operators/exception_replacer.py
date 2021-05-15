"Implementation of the exception-replacement operator."

from parso.python.tree import Name, PythonNode

from cosmic_ray.exceptions import CosmicRayTestingException

from .operator import Operator


class ExceptionReplacer(Operator):
    """An operator that modifies exception handlers."""

    def mutation_positions(self, node):
        if isinstance(node, PythonNode):
            if node.type == "except_clause":
                for name in self._name_nodes(node):
                    yield (name.start_pos, name.end_pos)

    def mutate(self, node, index):
        assert isinstance(node, PythonNode)
        assert node.type == "except_clause"

        name_nodes = self._name_nodes(node)
        assert index < len(name_nodes)
        name_nodes[index].value = CosmicRayTestingException.__name__
        return node

    @staticmethod
    def _name_nodes(node):
        if isinstance(node.children[1], Name):
            return (node.children[1],)

        atom = node.children[1]
        test_list = atom.children[1]
        return test_list.children[::2]

    @classmethod
    def examples(cls):
        return (
            (
                "try: raise OSError\nexcept OSError: pass",
                "try: raise OSError\nexcept {}: pass".format(CosmicRayTestingException.__name__),
            ),
            (
                "try: raise OSError\nexcept (OSError, ValueError): pass",
                "try: raise OSError\nexcept (OSError, {}): pass".format(CosmicRayTestingException.__name__),
                1,
            ),
            (
                "try: raise OSError\nexcept (OSError, ValueError, KeyError): pass",
                "try: raise OSError\nexcept (OSError, {}, KeyError): pass".format(CosmicRayTestingException.__name__),
                1,
            ),
            ("try: pass\nexcept: pass", "try: pass\nexcept: pass"),
        )
