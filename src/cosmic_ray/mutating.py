"""Support for making mutations to source code."""

import contextlib
import difflib
import logging
import traceback
from collections.abc import Iterable
from contextlib import contextmanager
from itertools import chain
from pathlib import Path

import cosmic_ray.plugins
from cosmic_ray.ast import Visitor, get_ast
from cosmic_ray.testing import run_tests
from cosmic_ray.util import read_python_source, restore_contents
from cosmic_ray.work_item import MutationSpec, TestOutcome, WorkResult, WorkerOutcome

log = logging.getLogger(__name__)


# pylint: disable=R0913
def mutate_and_test(mutations: Iterable[MutationSpec], test_command, timeout) -> WorkResult:
    """Apply a sequence of mutations, run thest tests, and reports the results.

    This is fundamentally the mutation(s)-and-test-run implementation at the heart of Cosmic Ray.

    There are three high-level ways that a worker can finish. First, it could fail exceptionally, meaning that some
    uncaught exception made its way from some part of the operation to terminate the function. This function will
    intercept all exceptions and return it in a non-exceptional structure.

    Second, the mutation machinery may determines that - for any of the mutations - there is no mutation to be made (e.g.
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
            file_changes: dict[Path, tuple[str, str]] = {}
            for mutation in mutations:
                operator_class = cosmic_ray.plugins.get_operator(mutation.operator_name)
                try:
                    operator_args = mutation.operator_args
                except AttributeError:
                    operator_args = {}
                operator = operator_class(**operator_args)

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

            test_outcome, output = run_tests(test_command, timeout)

            diffs = [
                _make_diff(original_code, mutated_code, module_path)
                for module_path, (original_code, mutated_code) in file_changes.items()
            ]

            result = WorkResult(
                output=output,
                diff="\n".join(chain(*diffs)),
                test_outcome=test_outcome,
                worker_outcome=WorkerOutcome.NORMAL,
            )

    except Exception:  # noqa # pylint: disable=broad-except
        return WorkResult(
            output=traceback.format_exc(), test_outcome=TestOutcome.INCOMPETENT, worker_outcome=WorkerOutcome.EXCEPTION
        )

    return result


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
    with restore_contents(module_path):
        original_code, mutated_code = apply_mutation(module_path, operator, occurrence)
        yield original_code, mutated_code


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
    return MutationVisitor.mutate_path(module_path, operator, occurrence)


def mutate_code(code, operator, occurrence):
    """Apply a specific mutation to a code string.

    Args:
        code: The code to mutate.
        operator: The `operator` instance to use.
        occurrence: The occurrence of the operator to apply.

    Returns:
        The mutated code, or None if no mutation was applied.
    """
    return MutationVisitor.mutate_code(code, operator, occurrence)


class MutationVisitor(Visitor):
    """Visitor that mutates a module with the specific occurrence of an operator.

    This will perform at most one mutation in a walk of an AST. If this performs
    a mutation as part of the walk, it will store the mutated node in the
    `mutant` attribute. If the walk does not result in any mutation, `mutant`
    will be `None`.

    Note that `mutant` is just the specifically mutated node. It will generally
    be a part of the larger AST which is returned from `walk()`.
    """

    @classmethod
    def mutate_code(cls, source, operator, occurence):
        ast = get_ast(source)
        visitor = cls(occurence, operator)
        mutated_ast = visitor.walk(ast)
        if not visitor.mutation_applied:
            return None
        return mutated_ast.get_code()

    @classmethod
    def mutate_path(cls, module_path, operator, occurrence):
        """Mutate a module in place on disk.

        Args:
            module_path (Path): The path to the module file.
            operator (Operator): The operator to apply.
            occurrence (int): The occurrence of the operator to apply.

        Returns:
            tuple[str, str|None]: The original code and the mutated code (or None)
        """
        log.info("Applying mutation: path=%s, op=%s, occurrence=%s", module_path, operator, occurrence)

        original_code = read_python_source(module_path)
        mutated_code = cls.mutate_code(original_code, operator, occurrence)

        if mutated_code is None:
            return original_code, None

        with module_path.open(mode="wt", encoding="utf-8") as handle:
            handle.write(mutated_code)
            handle.flush()

        return original_code, mutated_code

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
