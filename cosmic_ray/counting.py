"""Facilities for counting how many mutants will be created in a
cross-products of operators and modules.
"""

from .parsing import get_ast


class _CountingCore:
    """An operator core which simply counts how many times an operator finds a
    mutation site in a module.
    """
    def __init__(self):
        self.count = 0

    def visit_mutation_site(self, node, op):
        self.count += 1

    def repr_args(self):
        return []


def _count(module, op_cls):
    "Count mutants for a single module-operator pair."
    core = _CountingCore()
    op = op_cls(core)
    op.visit(get_ast(module))
    return core.count


def count_mutants(modules, operators):
    """Count how many mutations each operator will peform on each module.
    """
    return {
        mod: {
            op: _count(mod, op)
            for op in operators
        }
        for mod in modules
    }

