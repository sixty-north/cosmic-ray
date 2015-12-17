"""This is the body of the low-level worker tool.

A worker is intended to run as a process that imports a module, mutates it in
one location with one operator, runs the tests, reports the results, and dies.
"""

import importlib
import json
import logging
import subprocess

from .celery import app
from .importing import using_mutant
from .parsing import get_ast

LOG = logging.getLogger()


@app.task
def worker_task(*args):
    command = [
        'cosmic-ray',
        'worker',
    ] + args
    proc = subprocess.run(command,
                          stdout=subprocess.PIPE,
                          universal_newlines=True)
    result = json.loads(proc.stdout)
    return result


def worker(module_name,
           operator_class,
           occurrence,
           test_runner,
           timeout):
    """Mutate the OCCURRENCE-th site for OPERATOR_NAME in MODULE_NAME, run the
    tests, and report the results.

    Returns: A (`activation-record`, `test_runner.TestResult`) tuple if the
        tests were run, or None if there was no mutation (and hence no need to
        run tests).

    Raises:
        ImportError: If `module_name` can not be imported

    """
    # TODO: Timeout?

    module = importlib.import_module(module_name)
    module_ast = get_ast(module)
    operator = operator_class(occurrence)
    operator.visit(module_ast)

    if operator.activation_record:
        with using_mutant(module_name, module_ast):
            return (operator.activation_record,
                    test_runner())

    return None
