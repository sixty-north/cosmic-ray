"""This is the body of the low-level worker tool.

A worker is intended to run as a process that imports a module, mutates it in
one location with one operator, runs the tests, reports the results, and dies.
"""

import astunparse
import difflib
import importlib
import inspect
import logging
import sys
import traceback

from .importing import preserve_modules, using_ast
from .mutating import MutatingCore
from .parsing import get_ast
from .testing.test_runner import TestResult, Outcome

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
        with preserve_modules():
            module = importlib.import_module(module_name)
            module_source_file = inspect.getsourcefile(module)
            module_ast = get_ast(module)
            module_source = astunparse.unparse(module_ast)

            core = MutatingCore(occurrence)
            operator = operator_class(core)
            # note: after this step module_ast and modified_ast
            # appear to be the same
            modified_ast = operator.visit(module_ast)
            modified_source = astunparse.unparse(modified_ast)

            if not core.activation_record:
                return ('no-test', None)

            # generate a source diff to visualize how the mutation
            # operator has changed the code
            module_diff = ["--- mutation diff ---"]
            for line in difflib.unified_diff(
                            module_source.split('\n'),
                            modified_source.split('\n'),
                            fromfile="a" + module_source_file,
                            tofile="b" + module_source_file,
                            lineterm=""):
                module_diff.append(line)

        with using_ast(module_name, module_ast):
            results = test_runner()
            # append the diff to whatever result was returned
            res = results[1] or []
            res.extend(module_diff)
            results = TestResult(results[0], res)

        return ('normal',
                (core.activation_record,
                 results))

    except Exception:  # noqa
        res = traceback.format_exception(*sys.exc_info())
        res.extend(module_diff)
        results = [Outcome.INCOMPETENT, res]
        return ('exception', (None, results))
