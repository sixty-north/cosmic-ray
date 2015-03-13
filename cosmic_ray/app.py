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


def run_with_mutants(module, operator, func, q):
    with open(module.__file__, 'rt') as f:
        log.info('reading module {} from {}'.format(
            module.__name__, module.__file__))
        source = f.read()

    log.info('parsing module {}'.format(module.__name__))

    pristine_ast = ast.parse(source, module.__file__, 'exec')

    for record, mutant in operator.bombard(pristine_ast):
        try:
            new_mod = types.ModuleType(module.__name__)
            code = compile(mutant, module.__file__, 'exec')
            sys.modules[module.__name__] = new_mod
            exec(code,  new_mod.__dict__)
            result, data = func(module)
        except Exception as e:
            result = INCOMPETENT
            data = e

        q.put((record, result))


def run_test(test_dir, module):
    suite = unittest.TestLoader().discover(test_dir)
    result = unittest.TestResult()
    suite.run(result)
    if result.wasSuccessful():
        return (SURVIVED, result)
    else:
        return (KILLED, result)


def main(top_module, test_dir):
    # 1. Find all modules to be mutated
    modules = list(find_modules(top_module))

    # Remove those names from sys.modules. Tests will import them on
    # their own after mutation.
    for m in modules:
        del sys.modules[m.__name__]

    # 2. For each module, for each operator
    q = multiprocessing.Queue()

    for m in modules:
        for operator in all_operators():
            log.info('applying operator {}'.format(operator))
            p = multiprocessing.Process(
                target=run_with_mutants,
                args=(m, operator, partial(run_test, test_dir), q))
            p.start()
            p.join()

    while not q.empty():
        print(q.get())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1], sys.argv[2])
