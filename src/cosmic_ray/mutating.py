"""Support for making mutations to source code.
"""
import difflib
import traceback

import cosmic_ray.mutating
import cosmic_ray.plugins
from cosmic_ray.testing import run_tests
from cosmic_ray.work_item import TestOutcome, WorkerOutcome, WorkResult


from contextlib import contextmanager

from cosmic_ray.ast import get_ast, Visitor

# pylint: disable=R0913
def mutate_and_test(module_path,
           python_version,
           operator_name,
           occurrence,
           test_command,
           timeout):
    """Mutate the OCCURRENCE-th site for OPERATOR_NAME in MODULE_PATH, run the
    tests, and report the results.

    This is fundamentally the single-mutation-and-test-run implementation at the heart
    of Cosmic Ray.

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
        module_name: The path to the module to mutate
        python_version: The version of Python to use when interpreting the code in `module_path`.
            A string of the form "MAJOR.MINOR", e.g. "3.6" for Python 3.6.x.
        operator_name: The name of the operator plugin to use
        occurrence: The occurrence of the operator to apply
        test_command: The command to execute to run the tests
        timeout: The maximum amount of time (seconds) to let the tests run

    Returns: A WorkResult

    Raises: This will generally not raise any exceptions. Rather, exceptions
        will be reported using the 'exception' result-type in the return value.

    """
    try:
        operator_class = cosmic_ray.plugins.get_operator(operator_name)
        operator = operator_class(python_version)

        with cosmic_ray.mutating.use_mutation(module_path, operator,
                                              occurrence) as (original_code,
                                                              mutated_code):
            if mutated_code is None:
                return WorkResult(worker_outcome=WorkerOutcome.NO_TEST)

            test_outcome, output = run_tests(test_command, timeout)

            diff = _make_diff(original_code, mutated_code, module_path)

            return WorkResult(
                output=output,
                diff='\n'.join(diff),
                test_outcome=test_outcome,
                worker_outcome=WorkerOutcome.NORMAL)

    except Exception:  # noqa # pylint: disable=broad-except
        return WorkResult(
            output=traceback.format_exc(),
            test_outcome=TestOutcome.INCOMPETENT,
            worker_outcome=WorkerOutcome.EXCEPTION)


@contextmanager
def use_mutation(module_path, operator, occurrence):
    """A context manager that applies a mutation for the duration of a with-block.

    This applies a mutation to a file on disk, and after the with-block it put the unmutated code
    back in place.

    Args:
        module_path: The path to the module to mutate.
        operator: The `Operator` instance to use.
        occurrence: The occurrence of the operator to apply.

    Yields: A `(unmutated-code, mutated-code)` tuple to the with-block. If there was
        no mutation performed, the `mutated-code` is `None`.
    """
    original_code, mutated_code = apply_mutation(module_path, operator,
                                                 occurrence)
    try:
        yield original_code, mutated_code
    finally:
        with module_path.open(mode='wt', encoding='utf-8') as handle:
            handle.write(original_code)
            handle.flush()


def apply_mutation(module_path, operator, occurrence):
    """Apply a specific mutation to a file on disk.

    Args:
        module_path: The path to the module to mutate.
        operator: The `operator` instance to use.
        occurrence: The occurrence of the operator to apply.

    Returns: A `(unmutated-code, mutated-code)` tuple to the with-block. If there was
        no mutation performed, the `mutated-code` is `None`.
    """
    module_ast = get_ast(module_path, python_version=operator.python_version)
    original_code = module_ast.get_code()
    visitor = MutationVisitor(occurrence, operator)
    mutated_ast = visitor.walk(module_ast)

    mutated_code = None
    if visitor.mutation_applied:
        mutated_code = mutated_ast.get_code()
        with module_path.open(mode='wt', encoding='utf-8') as handle:
            handle.write(mutated_code)
            handle.flush()

    return original_code, mutated_code


class MutationVisitor(Visitor):
    """Visitor that mutates a module with the specific occurrence of an operator.

    This will perform at most one mutation in a walk of an AST. If this performs
    a mutation as part of the walk, it will store the mutated node in the
    `mutant` attribute. If the walk does not result in any mutation, `mutant`
    will be `None`.

    Note that `mutant` is just the specifically mutated node. It will generally
    be a part of the larger AST which is returned from `walk()`.
    """

    def __init__(self, occurrence, operator):
        self.operator = operator
        self._occurrence = occurrence
        self._count = 0
        self._mutation_applied = False

    @property
    def mutation_applied(self):
        "Whether this visitor has applied a mutation."
        return self._mutation_applied

    def visit(self, node):
        for index, _ in enumerate(self.operator.mutation_positions(node)):
            if self._count == self._occurrence:
                self._mutation_applied = True
                node = self.operator.mutate(node, index)
            self._count += 1

        return node


def _make_diff(original_source, mutated_source, module_path):
    module_diff = ["--- mutation diff ---"]
    for line in difflib.unified_diff(
            original_source.split('\n'),
            mutated_source.split('\n'),
            fromfile="a" + str(module_path),
            tofile="b" + str(module_path),
            lineterm=""):
        module_diff.append(line)
    return module_diff

