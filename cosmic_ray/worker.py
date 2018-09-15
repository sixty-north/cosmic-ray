"""This is the body of the low-level worker tool.

A worker is intended to run as a process that imports a module, mutates it in
one location with one operator, runs the tests, reports the results, and dies.
"""

import difflib
import importlib
import inspect
import logging
import multiprocessing.pool
import sys
import traceback

import astunparse

import cosmic_ray.compat.json
from cosmic_ray.importing import preserve_modules, using_ast
from cosmic_ray.mutating import MutatingCore
from cosmic_ray.parsing import get_ast
from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.util import StrEnum
from cosmic_ray.work_item import WorkItem


try:
    import typing      # the typing module does some fancy stuff at import time
                       # which we shall not do twice... by loading it here,
                       # preserve_modules does not delete it and therefore
                       # fancy stuff happens only once
except ImportError:
    pass

log = logging.getLogger()


class WorkerOutcome(StrEnum):
    """Possible outcomes for a worker.
    """
    NORMAL = 'normal'       # The worker exited normally, producing valid output
    EXCEPTION = 'exception' # The worker exited with an exception
    ABNORMAL = 'abnormal'   # The worker did not exit normally or with an exception (e.g. a segfault)
    NO_TEST = 'no-test'     # The worker had no test to run
    TIMEOUT = 'timeout'     # The worker timed out
    SKIPPED = 'skipped'     # The job was skipped (worker was not executed)


def worker(module_name,
           operator,
           occurrence,
           test_runner):
    """Mutate the OCCURRENCE-th site for OPERATOR_CLASS in MODULE_NAME, run the
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

    Args:
        module_name: The name of the module to be mutated
        operator: The operator be applied
        occurrence: The occurrence of the operator to apply
        test_runner: The test runner plugin to use

    Returns: A WorkItem

    Raises: This will generally not raise any exceptions. Rather, exceptions
        will be reported using the 'exception' result-type in the return value.

    """
    try:
        # TODO: What should we be doing here? This feels too hacky.
        sys.path.insert(0, '')

        with preserve_modules():
            module = importlib.import_module(module_name)
            module_source_file = inspect.getsourcefile(module)
            module_ast = get_ast(module)
            module_source = astunparse.unparse(module_ast)

            core = MutatingCore(occurrence)
            operator = operator(core)
            # note: after this step module_ast and modified_ast
            # appear to be the same
            modified_ast = operator.visit(module_ast)
            modified_source = astunparse.unparse(modified_ast)

            if not core.activation_record:
                return WorkItem(
                    worker_outcome=WorkerOutcome.NO_TEST)

            # generate a source diff to visualize how the mutation
            # operator has changed the code
            module_diff = ["--- mutation diff ---"]
            for line in difflib.unified_diff(module_source.split('\n'),
                                             modified_source.split('\n'),
                                             fromfile="a" + module_source_file,
                                             tofile="b" + module_source_file,
                                             lineterm=""):
                module_diff.append(line)

        with using_ast(module_name, module_ast):
            item = test_runner()

        item.update({
            'diff': module_diff,
            'worker_outcome': WorkerOutcome.NORMAL,
            'occurrence': core.activation_record['occurrence'],
            'line_number': core.activation_record['line_number'],
        })
        return item

    except Exception:  # noqa # pylint: disable=broad-except
        return WorkItem(
            data=traceback.format_exception(*sys.exc_info()),
            test_outcome=TestOutcome.INCOMPETENT,
            worker_outcome=WorkerOutcome.EXCEPTION)


def _worker_multiprocessing_wrapper(pipe, *args, **kwargs):
    """Wrapper for launching workers with multiprocessing.

    Args:
        pipe: The `multiprocessing.Pipe` for sending results.
    """
    item = worker(*args, **kwargs)
    pipe.send(item)


def execute_work_item(work_item,
                      timeout,
                      config):
    """Execute the mutation and tests described in a `WorkItem`.

    Args:
        work_item: The WorkItem describing the work to do.
        timeout: The maximum amount of time (seconds) to allow the subprocess
            to run.
        config: The configuration for the run.

    Returns: An updated `WorkItem` with the results of the tests.

    """
    parent_conn, child_conn = multiprocessing.Pipe()
    proc = multiprocessing.Process(
        target=_worker_multiprocessing_wrapper,
        args=(child_conn,
              work_item.module,
              cosmic_ray.plugins.get_operator(work_item.operator),
              work_item.occurrence,
              cosmic_ray.plugins.get_test_runner(
                  config['test-runner', 'name'],
                  config['test-runner', 'args'])))

    proc.start()

    if parent_conn.poll(timeout):
        result = parent_conn.recv()
        work_item.update({
            k: v
            for k, v
            in result.items()
            if v is not None
        })
    else:  # timeout
        work_item.worker_outcome = WorkerOutcome.TIMEOUT
        work_item.data = timeout
        proc.terminate()

    proc.join()

    # TODO: This is in an awkward place now...we don't use the command any
    # more. Where would be a better place? Or should we generate this another
    # way? This command line is useful for debugging, but meaningless here.
    command = 'cosmic-ray worker {module} {operator} {occurrence}'.format(
        **work_item)
    work_item.command_line = command
    return work_item
