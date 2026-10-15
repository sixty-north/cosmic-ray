"Implementation of the exception-replacement operator."

from parso.python.tree import Name, PythonNode

from cosmic_ray.exceptions import CosmicRayTestingException

from .operator import Example, Operator


class ExceptionReplacer(Operator):
    """An operator that modifies exception handlers."""

    def mutation_positions(self, node):
        if isinstance(node, PythonNode):
            if node.type == "except_clause":
                for expression in self._exception_expressions(node):
                    yield (expression.start_pos, expression.end_pos)

    def mutate(self, node, index):
        assert isinstance(node, PythonNode)
        assert node.type == "except_clause"

        expressions = self._exception_expressions(node)
        assert index < len(expressions)
        expression = expressions[index]
        if isinstance(expression, Name):
            expression.value = CosmicRayTestingException.__name__
            return node

        replacement = Name(
            CosmicRayTestingException.__name__,
            expression.start_pos,
            prefix=expression.get_first_leaf().prefix,
        )
        parent = expression.parent
        assert parent is not None
        parent.children[parent.children.index(expression)] = replacement
        replacement.parent = parent
        return node

    @staticmethod
    def _exception_expressions(node):
        expression = node.children[1]
        if isinstance(expression, Name) or expression.type != "atom" or expression.children[0].value != "(":
            return (expression,)

        inner = expression.children[1]
        if isinstance(inner, Name) or inner.type != "testlist_comp":
            return (inner,)
        return inner.children[::2]

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
            Example(
                "try: raise OSError\nexcept subprocess.TimeoutExpired: pass",
                f"try: raise OSError\nexcept {CosmicRayTestingException.__name__}: pass",
            ),
            Example(
                "try: raise OSError\nexcept (OSError, subprocess.TimeoutExpired) as exc: pass",
                f"try: raise OSError\nexcept (OSError, {CosmicRayTestingException.__name__}) as exc: pass",
                occurrence=1,
            ),
            Example("try: pass\nexcept: pass", "try: pass\nexcept: pass"),
        )
