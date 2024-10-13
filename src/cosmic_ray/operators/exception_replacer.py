"Implementation of the exception-replacement operator."

from parso.python.tree import Name, PythonNode

from cosmic_ray.exceptions import CosmicRayTestingException

from .operator import Example, Operator


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
        if isinstance(test_list, Name):
            return (test_list,)
        return test_list.children[::2]

    @classmethod
    def examples(cls):
        return (
            Example(
                "try: raise OSError\nexcept OSError: pass",
                f"try: raise OSError\nexcept {CosmicRayTestingException.__name__}: pass",
            ),
            Example(
                "try: raise OSError\nexcept (OSError): pass",
                f"try: raise OSError\nexcept ({CosmicRayTestingException.__name__}): pass",
            ),
            Example(
                "try: raise OSError\nexcept (OSError, ValueError): pass",
                f"try: raise OSError\nexcept (OSError, {CosmicRayTestingException.__name__}): pass",
                occurrence=1,
            ),
            Example(
                "try: raise OSError\nexcept (OSError, ValueError, KeyError): pass",
                f"try: raise OSError\nexcept (OSError, {CosmicRayTestingException.__name__}, KeyError): pass",
                occurrence=1,
            ),
            Example("try: pass\nexcept: pass", "try: pass\nexcept: pass"),
        )
