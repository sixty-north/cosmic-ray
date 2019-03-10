"Implementation of the exception-replacement operator."

import builtins

from parso.python.tree import Name, PythonNode

from .operator import Operator


class CosmicRayTestingException(Exception):
    "A special exception we throw that nobody should be trying to catch."


# We inject this into builtins so we can easily replace other exceptions
# without necessitating the import of other modules.
setattr(builtins, CosmicRayTestingException.__name__,
        CosmicRayTestingException)


class ExceptionReplacer(Operator):
    """An operator that modifies exception handlers."""

    def mutation_positions(self, node):
        if isinstance(node, PythonNode):
            if node.type == 'except_clause':
                for name in self._name_nodes(node):
                    yield (name.start_pos, name.end_pos)

    def mutate(self, node, index):
        assert isinstance(node, PythonNode)
        assert node.type == 'except_clause'

        name_nodes = self._name_nodes(node)
        assert index < len(name_nodes)
        name_nodes[index].value = CosmicRayTestingException.__name__
        return node

    @staticmethod
    def _name_nodes(node):
        if isinstance(node.children[1], Name):
            return (node.children[1], )

        atom = node.children[1]
        test_list = atom.children[1]
        return test_list.children[::2]

    @classmethod
    def examples(cls):
        return (
            ('try: raise OSError\nexcept OSError: pass',
             'try: raise OSError\nexcept CosmicRayTestingException: pass'),
            ('try: raise OSError\nexcept (OSError, ValueError): pass',
             'try: raise OSError\nexcept (OSError, CosmicRayTestingException): pass',
             1),
            ('try: raise OSError\nexcept (OSError, ValueError, KeyError): pass',
             'try: raise OSError\nexcept (OSError, CosmicRayTestingException, KeyError): pass',
             1),
            ('try: pass\nexcept: pass',
             'try: pass\nexcept: pass'),
        )
