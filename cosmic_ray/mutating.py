import ast
from enum import Enum
import logging
import sys
import types

log = logging.getLogger()


class Outcome(Enum):
    SURVIVED = 'survived'
    KILLED = 'killed'
    INCOMPETENT = 'incompetent'


def run_with_mutants(module_file, module_name, operator, func, q):
    """Run a function for each mutatation of a module.

    Mutate the module specified by `module_file` and `module_name`
    using `operator`. For each mutation, install that mutant into the
    module registry and then run `func`.

    Each run of `func` will insert a new element into `q` of the form:

        (activation-record, outcome, data)

    `activation-record` is a
    `cosmic_ray.operators.operator.ActivationRecord` describing the
    location and nature of the mutation.

    `outcome` is one of `SURVIVED`, `KILLED`, or `INCOMPETENT`
    depending on the fate of the mutant.

    `data` is any data describing the test run.

    This function is designed to be run in its own process,
    specifically via the `multiprocessing` module.

    """
    with open(module_file, 'rt') as f:
        log.info('reading module {} from {}'.format(
            module_name, module_file))
        source = f.read()

    log.info('parsing module {}'.format(module_name))

    pristine_ast = ast.parse(source, module_file, 'exec')

    log.info('{} successfully parsed'.format(module_name))

    for record, mutant in operator.bombard(pristine_ast):
        record['filename'] = module_file
        try:
            new_mod = types.ModuleType(module_name)
            code = compile(mutant, module_file, 'exec')
            sys.modules[module_name] = new_mod
            exec(code,  new_mod.__dict__)
            passed, result = func()
            q.put((record,
                   Outcome.SURVIVED if passed else Outcome.KILLED,
                   result))
        except Exception as e:
            q.put((record,
                   Outcome.INCOMPETENT,
                   str(e)))
