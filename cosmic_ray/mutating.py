"""Support for making mutations to source code.
"""
from contextlib import contextmanager

from cosmic_ray.ast import get_ast, Visitor


@contextmanager
def use_mutation(module_path, operator, occurrence):
    """A context manager that applies a mutation for the duration of a with-block.

    This applies a mutation to a file on disk, and after the with-block it put the unmutated code
    back in place.

    Args:
        module_path: The path to the module to mutate.
        operator: The `Operator` instance to use.
        occurrence: The occurrence of the operator to apply.

    Yields: A `(unmutated-code, mutated-code)` tuple to the with-block. If there was
        no mutation performed, the `mutated-code` is `None`.
    """
    original_code, mutated_code = apply_mutation(module_path, operator,
                                                 occurrence)
    try:
        yield original_code, mutated_code
    finally:
        with module_path.open(mode='wt', encoding='utf-8') as handle:
            handle.write(original_code)
            handle.flush()


def apply_mutation(module_path, operator, occurrence):
    """Apply a specific mutation to a file on disk.

    Args:
        module_path: The path to the module to mutate.
        operator: The `operator` instance to use.
        occurrence: The occurrence of the operator to apply.

    Returns: A `(unmutated-code, mutated-code)` tuple to the with-block. If there was
        no mutation performed, the `mutated-code` is `None`.
    """
    module_ast = get_ast(module_path, python_version=operator.python_version)
    original_code = module_ast.get_code()
    visitor = MutationVisitor(occurrence, operator)
    mutated_ast = visitor.walk(module_ast)

    mutated_code = None
    if visitor.mutation_applied:
        mutated_code = mutated_ast.get_code()
        with module_path.open(mode='wt', encoding='utf-8') as handle:
            handle.write(mutated_code)
            handle.flush()

    return original_code, mutated_code


class MutationVisitor(Visitor):
    """Visitor that mutates a module with the specific occurrence of an operator.

    This will perform at most one mutation in a walk of an AST. If this performs
    a mutation as part of the walk, it will store the mutated node in the
    `mutant` attribute. If the walk does not result in any mutation, `mutant`
    will be `None`.

    Note that `mutant` is just the specifically mutated node. It will generally
    be a part of the larger AST which is returned from `walk()`.
    """

    def __init__(self, occurrence, operator):
        self.operator = operator
        self._occurrence = occurrence
        self._count = 0
        self._mutation_applied = False

    @property
    def mutation_applied(self):
        "Whether this visitor has applied a mutation."
        return self._mutation_applied

    def visit(self, node):
        for index, _ in enumerate(self.operator.mutation_positions(node)):
            if self._count == self._occurrence:
                self._mutation_applied = True
                node = self.operator.mutate(node, index)
            self._count += 1

        return node
