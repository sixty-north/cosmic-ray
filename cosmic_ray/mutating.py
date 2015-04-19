import ast
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
import logging
import sys
import types
from collections import namedtuple

from .importing import using_mutant


log = logging.getLogger()


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
        with open(module.__file__, 'rt', encoding='utf-8') as f:
            log.info('reading module {} from {}'.format(
                module.__name__, module.__file__))
            source = f.read()

        pristine_ast = ast.parse(source, module.__file__, 'exec')

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
    module_name, module_file, _, _, mutant = mutation_record
    with using_mutant(module_name, mutant):
        return func()
