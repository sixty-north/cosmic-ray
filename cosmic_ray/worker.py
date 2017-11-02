"""This is the body of the low-level worker tool.

A worker is intended to run as a process that imports a module, mutates it in
one location with one operator, runs the tests, reports the results, and dies.
"""

import difflib
import importlib
import inspect
import json
import logging
import subprocess
import sys
import traceback

import astunparse

from .config import serialize_config
from .importing import preserve_modules, using_ast
from .mutating import MutatingCore
from .parsing import get_ast
from .testing.test_runner import TestOutcome
from .work_record import WorkRecord

LOG = logging.getLogger()


class WorkerOutcome:  # pylint: disable=too-few-public-methods
    """Possible outcomes for a worker.
    """
    NORMAL = 'normal'
    EXCEPTION = 'exception'
    NO_TEST = 'no-test'
    TIMEOUT = 'timeout'


def worker(module_name,
           operator_class,
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

    Returns: a WorkRecord

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
                return WorkRecord(
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
            rec = test_runner()

        rec.update({
            'diff': module_diff,
            'worker_outcome': WorkerOutcome.NORMAL
        })
        rec.update(core.activation_record)
        return rec

    except Exception:  # noqa # pylint: disable=broad-except
        return WorkRecord(
            data=traceback.format_exception(*sys.exc_info()),
            test_outcome=TestOutcome.INCOMPETENT,
            worker_outcome=WorkerOutcome.EXCEPTION)


def worker_process(work_record,
                   timeout,
                   config):
    """Run `cosmic-ray worker` in a subprocess and return the results,
    passing `config` to it via stdin.

    Returns: An updated WorkRecord

    """
    # The work_record param may come as just a dict (e.g. if it arrives over
    # celery), so we reconstruct a WorkRecord to make it easier to work with.
    work_record = WorkRecord(work_record)

    command = 'cosmic-ray worker {module} {operator} {occurrence}'.format(
        **work_record)

    LOG.info('executing: %s', command)

    proc = subprocess.Popen(command.split(),
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
    config_string = serialize_config(config)
    try:
        outs, _ = proc.communicate(input=config_string, timeout=timeout)
        result = json.loads(outs)
        work_record.update({
            k: v
            for k, v
            in result.items()
            if v is not None
        })
    except subprocess.TimeoutExpired as exc:
        work_record.worker_outcome = WorkerOutcome.TIMEOUT
        work_record.data = exc.timeout
        proc.kill()
    except json.JSONDecodeError as exc:
        work_record.worker_outcome = WorkerOutcome.EXCEPTION
        work_record.data = exc

    work_record.command_line = command
    return work_record
