"""This is the body of the low-level worker tool.

A worker is intended to run as a process that imports a module, mutates it in
one location with one operator, runs the tests, reports the results, and dies.
"""

import importlib
import logging
import sys
import traceback

from .importing import using_mutant
from .mutating import MutatingCore
from .parsing import get_ast

LOG = logging.getLogger()


def worker(module_name,
           operator_class,
           occurrence,
           test_runner):
    """Mutate the OCCURRENCE-th site for OPERATOR_NAME in MODULE_NAME, run the
    tests, and report the results.

    This is fundamentally the single-mutation-and-test-run process
    implementation.

    There are three high-level ways that a worker can finish. First, it could
    fail exceptionally, meaning that some uncaught exception made its way from
    some part of the operation to terminate the function. This function will
    intercept all exceptions and return it in a non-exceptional structure.

    Second, the mutation testing machinery may determine that there is no
    OCCURENCE-th instance for OPERATOR_NAME in the module under test. In this
    case there is no way to report a test result (i.e. killed, survived, or
    incompetent) so a special value is returned indicating that no mutation is
    possible.

    Finally, and hopefully normally, the worker will find that it can run a
    test. It will do so and report back the result - killed, survived, or
    incompetent - in a structured way.

    Returns: A tuple `(result-type, data)`. `result-type` is either the string
        'exception', 'no-test', or 'normal'.

        If the result is 'exception' then data will be the tuple returned by
        `sys.exc_info()`.

        If the result is 'no-test' then data will be `None`.

        If the result is 'normal' then the data will be a tuple of
        (`activation-record`, `test_runner.TestResult`).

    Raises: This will generally not raise any exceptions. Rather, exceptions
        will be reported using the 'exception' result-type in the return value.

    """
    try:
        module = importlib.import_module(module_name)
        module_ast = get_ast(module)
        core = MutatingCore(occurrence)
        operator = operator_class(core)
        operator.visit(module_ast)

        if not core.activation_record:
            return ('no-test', None)

        with using_mutant(module_name, module_ast):
            results = test_runner()

        return ('normal',
                (core.activation_record,
                 results))

    except Exception:
        return ('exception',
                traceback.format_exception(*sys.exc_info()))
