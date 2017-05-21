import ast

from .operator import Operator


class ExceptionReplacer(Operator):

    """An operator that modifies exception handlers."""

    def visit_ExceptHandler(self, node):  # noqa
        return self.visit_mutation_site(node)

    def mutate(self, node, _):
        """Modify the exception handler with another exception type."""
        except_id = 'TypeError' if node.name.id == 'SystemError' else \
            'SystemError'
        except_type = ast.Name(id=except_id, ctx=ast.Load())
        new_node = ast.ExceptHandler(type=except_type, name=node.name,
                                     body=node.body)
        return new_node