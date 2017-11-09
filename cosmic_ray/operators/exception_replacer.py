"Implementation of the exception-replacement operator."

import ast
import builtins

from .operator import Operator


class CosmicRayTestingException(Exception):
    "A special exception we throw that nobody should be trying to catch."
    pass


# We inject this into builtins so we can easily replace other exceptions
# without necessitating the import of other modules.
setattr(builtins,
        CosmicRayTestingException.__name__,
        CosmicRayTestingException)


class ExceptionReplacer(Operator):
    """An operator that modifies exception handlers."""

    def visit_ExceptHandler(self, node):  # noqa # pylint: disable=invalid-name
        "Visit an exception handler node."
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Modify the exception handler with another exception type."""
        except_id = CosmicRayTestingException.__name__
        except_type = ast.Name(id=except_id, ctx=ast.Load())
        new_node = ast.ExceptHandler(type=except_type, name=node.name,
                                     body=node.body)
        return new_node
