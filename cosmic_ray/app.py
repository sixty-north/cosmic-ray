# Find all of the modules that need to be mutated
# Create ASTs for all of the modules
# Foreach AST:
#    foreach operation:
#        foreach location in AST where op applies:
#            apply op to location
#            Make that AST active/replace old module with new
#            run all tests
#            If not failures, mutant survived!

import ast
from functools import partial
import logging
import multiprocessing
import sys
import types
import unittest

from cosmic_ray.find_modules import find_modules
from cosmic_ray.operators import all_operators

log = logging.getLogger()

SURVIVED = 'survived'
KILLED = 'killed'
INCOMPETENT = 'incompetent'


def run_with_mutants(module_file, module_name, operator, func, q):
    with open(module_file, 'rt') as f:
        log.info('reading module {} from {}'.format(
            module_name, module_file))
        source = f.read()

    log.info('parsing module {}'.format(module_name))

    pristine_ast = ast.parse(source, module_file, 'exec')

    log.info('{} successfully parsed'.format(module_name))

    for record, mutant in operator.bombard(pristine_ast):
        try:
            new_mod = types.ModuleType(module_name)
            code = compile(mutant, module_file, 'exec')
            sys.modules[module_name] = new_mod
            exec(code,  new_mod.__dict__)
            q.put(func())
        except Exception as e:
            q.put((INCOMPETENT, str(e)))


def run_test(test_dir):
    suite = unittest.TestLoader().discover(test_dir)
    result = unittest.TestResult()
    suite.run(result)
    if result.wasSuccessful():
        return SURVIVED, str(result)
    else:
        return KILLED, str(result)


def main(top_module, test_dir):
    # 1. Find all modules to be mutated
    modules = list(find_modules(top_module))

    # Remove those names from sys.modules. Tests will import them on
    # their own after mutation.
    for m in modules:
        del sys.modules[m.__name__]

    test_runner = partial(run_test, test_dir)

    mp_mgr = multiprocessing.Manager()
    response_queue = mp_mgr.Queue()

    with multiprocessing.Pool(4) as p:
        # results = p.starmap(
        #     run_with_mutants,
        #     [[m, op, test_runner]
        #      for m in modules
        #      for op in all_operators()])
        for m in modules:
            for op in all_operators():
                log.info('applying operator {}'.format(op))
                p.apply(
                    run_with_mutants,
                    (m.__file__,
                     m.__name__,
                     op,
                     test_runner,
                     response_queue))

    while not response_queue.empty():
        print(response_queue.get())

if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    main(sys.argv[1], sys.argv[2])
