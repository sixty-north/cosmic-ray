import ast
import logging
from collections import namedtuple

from .importing import using_mutant
from .parsing import get_ast


LOG = logging.getLogger()


MutationRecord = namedtuple('MutationRecord', ['module_name',
                                               'module_file',
                                               'operator',
                                               'activation_record',
                                               'mutant'])


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
