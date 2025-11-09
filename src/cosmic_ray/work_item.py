"""Classes for describing work and results."""

import enum
from pathlib import Path
from typing import Any, Optional

from attrs import define, field


class StrEnum(str, enum.Enum):
    "An Enum subclass with str values."


class WorkerOutcome(StrEnum):
    """Possible outcomes for a worker."""

    NORMAL = "normal"  # The worker exited normally, producing valid output
    EXCEPTION = "exception"  # The worker exited with an exception
    ABNORMAL = "abnormal"  # The worker did not exit normally or with an exception (e.g. a segfault)
    NO_TEST = "no-test"  # The worker had no test to run
    SKIPPED = "skipped"  # The job was skipped (worker was not executed)


class TestOutcome(StrEnum):
    """A enum of the possible outcomes for any mutant test run."""

    SURVIVED = "survived"
    KILLED = "killed"
    INCOMPETENT = "incompetent"


@define(frozen=True)
class WorkResult:
    """The result of a single mutation and test run."""

    worker_outcome: WorkerOutcome = field()
    output: Optional[str] = field(default=None)
    test_outcome: Optional[TestOutcome] = field(default=None)
    diff: Optional[str] = field(default=None)

    def __attrs_post_init__(self):
        if self.worker_outcome is None:
            raise ValueError("Worker outcome must always have a value.")

        if self.test_outcome is not None:
            object.__setattr__(self, "test_outcome", TestOutcome(self.test_outcome))

        object.__setattr__(self, "worker_outcome", WorkerOutcome(self.worker_outcome))

    @property
    def is_killed(self):
        "Whether the mutation should be considered 'killed'"
        return self.test_outcome != TestOutcome.SURVIVED


@define(frozen=True)
class MutationSpec:
    "Description of a single mutation."

    module_path: Path = field(converter=Path)
    operator_name: str = field()
    occurrence: int = field(converter=int)
    start_pos: tuple[int, int] = field()
    end_pos: tuple[int, int] = field()
    operator_args: dict[str, Any] = field(factory=dict)

    @end_pos.validator
    def _validate_positions(self, attribute, value):
        start_line, start_col = self.start_pos
        end_line, end_col = value

        if start_line > end_line or (start_line == end_line and start_col >= end_col):
            raise ValueError("End position must come after start position.")


@define(frozen=True)
class WorkItem:
    """A collection (possibly empty) of mutations to perform for a single test.

    This ability to perform more than one mutation for a single test run is how we support
    higher-order mutations.
    """

    job_id: str = field()
    mutations: tuple[MutationSpec, ...] = field(converter=tuple)

    @classmethod
    def single(cls, job_id, mutation: MutationSpec):
        """Construct a WorkItem with a single mutation.

        Args:
            job_id: The ID of the job.
            mutation: The single mutation for the WorkItem.

        Returns:
            A new `WorkItem` instance.
        """
        return cls(job_id, (mutation,))
