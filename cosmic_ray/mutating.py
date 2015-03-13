import ast
import logging
import sys
import types

log = logging.getLogger()

SURVIVED = 'survived'
KILLED = 'killed'
INCOMPETENT = 'incompetent'


def run_with_mutants(module_file, module_name, operator, func, q):
    """Run a function for each mutatation of a module.

    Mutate the module specified by `module_file` and `module_name`
    using `operator`. For each mutation, install that mutant into the
    module registry and then run `func`, putting `func`'s return value
    into the queue `q`.

    If `func` raises an exception, then a tuple (INCOMPETENT,
    exception-info) is placed into `q`.

    This is designed to be run in its own process, specifically via
    the `multiprocessing` module.
    """
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
            passed, result = func()
            q.put((SURVIVED if passed else KILLED,
                   result))
        except Exception as e:
            q.put((INCOMPETENT, str(e)))
