"""Support for making mutations to source code.
"""
import contextlib
import difflib
from itertools import chain
import traceback
from contextlib import contextmanager
import logging
from typing import Iterable

import cosmic_ray.plugins
from cosmic_ray.ast import Visitor, get_ast
from cosmic_ray.testing import run_tests
from cosmic_ray.work_item import MutationSpec, TestOutcome, WorkerOutcome, WorkResult

log = logging.getLogger(__name__)

# pylint: disable=R0913
async def mutate_and_test(mutations: Iterable[MutationSpec], test_command, timeout) -> WorkResult:
    """Apply a sequence of mutations, run thest tests, and reports the results.

    This is fundamentally the mutation(s)-and-test-run implementation at the heart of Cosmic Ray.

    There are three high-level ways that a worker can finish. First, it could fail exceptionally, meaning that some
    uncaught exception made its way from some part of the operation to terminate the function. This function will
    intercept all exceptions and return it in a non-exceptional structure.

    Second, the mutation machinery may determines that - for any of the mutations - there is mutation to be made (e.g.
    the 'occurrence' is too high).  In this case there is no way to report a test result (i.e. killed, survived, or
    incompetent) so a special value is returned indicating that no mutation is possible.

    Finally, and hopefully normally, the worker will find that it can run a test. It will do so and report back the
    result - killed, survived, or incompetent - in a structured way.

    Args:
        mutations: An iterable of ``MutationSpec``\\s describing the mutations to make.
        test_command: The command to execute to run the tests
        timeout: The maximum amount of time (seconds) to let the tests run

    Returns:
        A ``WorkResult``.

    Raises:
        This will generally not raise any exceptions. Rather, exceptions will be reported using the 'exception'
        result-type in the return value.

    """
    try:
        with contextlib.ExitStack() as stack:
            file_changes = {}
            for mutation in mutations:
                operator_class = cosmic_ray.plugins.get_operator(mutation.operator_name)
                operator = operator_class()
                (previous_code, mutated_code) = stack.enter_context(
                    use_mutation(mutation.module_path, operator, mutation.occurrence)
                )

                # If there's no mutated code, then no mutation was possible.
                if mutated_code is None:
                    return WorkResult(
                        worker_outcome=WorkerOutcome.NO_TEST,
                    )

                original_code, _ = file_changes.get(mutation.module_path, (previous_code, mutated_code))
                file_changes[mutation.module_path] = original_code, mutated_code

            test_outcome, output = await run_tests(test_command, timeout)

            diffs = [
                _make_diff(original_code, mutated_code, module_path)
                for module_path, (original_code, mutated_code) in file_changes.items()
            ]

            return WorkResult(
                output=output,
                diff="\n".join(chain(*diffs)),
                test_outcome=test_outcome,
                worker_outcome=WorkerOutcome.NORMAL,
            )

    except Exception:  # noqa # pylint: disable=broad-except
        return WorkResult(
            output=traceback.format_exc(), test_outcome=TestOutcome.INCOMPETENT, worker_outcome=WorkerOutcome.EXCEPTION
        )


@contextmanager
def use_mutation(module_path, operator, occurrence):
    """A context manager that applies a mutation for the duration of a with-block.

    This applies a mutation to a file on disk, and after the with-block it put the unmutated code
    back in place.

    Args:
        module_path: The path to the module to mutate.
        operator: The `Operator` instance to use.
        occurrence: The occurrence of the operator to apply.

    Yields:
        A `(unmutated-code, mutated-code)` tuple to the with-block. If there was no
        mutation performed, the `mutated-code` is `None`.
    """
    # TODO: Could/should use async?
    original_code, mutated_code = apply_mutation(module_path, operator, occurrence)
    try:
        yield original_code, mutated_code
    finally:
        with module_path.open(mode="wt", encoding="utf-8") as handle:
            handle.write(original_code)
            handle.flush()


def apply_mutation(module_path, operator, occurrence):
    """Apply a specific mutation to a file on disk.

    Args:
        module_path: The path to the module to mutate.
        operator: The `operator` instance to use.
        occurrence: The occurrence of the operator to apply.

    Returns:
        A `(unmutated-code, mutated-code)` tuple to the with-block. If there was
        no mutation performed, the `mutated-code` is `None`.
    """
    log.info("Applying mutation: path=%s, op=%s, occurrence=%s", module_path, operator, occurrence)
    module_ast = get_ast(module_path)
    original_code = module_ast.get_code()
    visitor = MutationVisitor(occurrence, operator)
    mutated_ast = visitor.walk(module_ast)

    mutated_code = None
    if visitor.mutation_applied:
        mutated_code = mutated_ast.get_code()
        with module_path.open(mode="wt", encoding="utf-8") as handle:
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
        original_source.split("\n"),
        mutated_source.split("\n"),
        fromfile="a" + str(module_path),
        tofile="b" + str(module_path),
        lineterm="",
    ):
        module_diff.append(line)
    return module_diff
