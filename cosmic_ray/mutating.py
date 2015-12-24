import ast
import copy
import itertools
import logging
from collections import namedtuple

from .importing import using_mutant
from .parsing import get_ast
from .util import get_line_number


LOG = logging.getLogger()


MutationRecord = namedtuple('MutationRecord', ['module_name',
                                               'module_file',
                                               'operator',
                                               'activation_record',
                                               'mutant'])


def _full_module_name(obj):
    return '{}.{}'.format(
        obj.__class__.__module__,
        obj.__class__.__name__)


class MutatingCore:
    """An `Operator` core which performs mutation of ASTs.

    This core is instantiated with a target count N. The Nth time the operator
    using the core calls `visit_mutation_site()`, this core will set the
    `activation_record` attribute and perform a mutation. In other words, this
    will mutate the `target`-th instance of an operator's mutation candidates
    if such a candidate exists. If there is no `target`-th candidate then
    `activation_record` will remain `None` and no mutation will occur.

    """
    def __init__(self, target):
        self._target = target
        self._count = 0
        self._activation_record = None

    @property
    def activation_record(self):
        """The activation record for the operator.

        The activation record is a dict describing where and how the
        operator was applied.
        """
        return self._activation_record

    def visit_mutation_site(self, node, op):
        """Potentially mutate `node`, returning the mutated version.

        `Operator` calls this when AST iteration reaches a
        potential mutation site. If that site is scheduled for
        mutation, the subclass instance will be asked to perform the
        mutation.
        """
        if self._count == self._target:
            self._activation_record = {
                'operator': _full_module_name(self),
                'description': str(self),
                'line_number': get_line_number(node)
            }

            old_node = node
            node = op.mutate(old_node)
            ast.copy_location(node, old_node)

        self._count += 1
        return node

    def repr_args(self):
        return [('target', self._target)]

    @classmethod
    def bombard(cls, node):
        """Bombard `node` with cosmic rays, generating a sequence of odious
        mutants.

        The returns an iterable sequence of mutated copies of `node`,
        with one mutant for each potential mutation site in `node`
        with respect to the `Operator` subclass which is performing
        the mutations.
        """
        for target in itertools.count():
            operator = cls(target)
            mutant = operator.visit(copy.deepcopy(node))
            if not operator.activation_record:
                break

            yield operator.activation_record, mutant


def create_mutants(modules, operators):
    """Mutate `modules` with `operators`.

    Returns an iterable of `MutationRecord`s, one for each application
    of an operator to a location in a module.

    """
    for module in modules:
        pristine_ast = get_ast(module)

        for operator in operators:
            for activation_record, mutant in operator.bombard(pristine_ast):
                yield MutationRecord(module_name=module.__name__,
                                     module_file=module.__file__,
                                     operator=operator,
                                     activation_record=activation_record,
                                     mutant=mutant)


def run_with_mutant(func, mutation_record):
    """Install the mutation record and run the callable `func`, returning
    its result.
    """
    module_name, _, _, _, mutant = mutation_record
    with using_mutant(module_name, mutant):
        return func()
