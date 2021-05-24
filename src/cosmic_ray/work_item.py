"""Classes for describing work and results.
"""
import dataclasses
import enum
import pathlib
from pathlib import Path
from typing import Optional, Tuple


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


@dataclasses.dataclass(frozen=True)
class WorkResult:
    """The result of a single mutation and test run."""

    worker_outcome: WorkerOutcome
    output: Optional[str] = None
    test_outcome: Optional[TestOutcome] = None
    diff: Optional[str] = None

    def __post_init__(self):
        if self.worker_outcome is None:
            raise ValueError("Worker outcome must always have a value.")

        if self.test_outcome is not None:
            object.__setattr__(self, "test_outcome", TestOutcome(self.test_outcome))

        object.__setattr__(self, "worker_outcome", WorkerOutcome(self.worker_outcome))

    @property
    def is_killed(self):
        "Whether the mutation should be considered 'killed'"
        return self.test_outcome != TestOutcome.SURVIVED


@dataclasses.dataclass(frozen=True)
class MutationSpec:
    "Description of a single mutation."
    module_path: Path
    operator_name: str
    occurrence: int

    # pylint: disable=R0913
    def __post_init__(self):
        object.__setattr__(self, "module_path", pathlib.Path(self.module_path))
        object.__setattr__(self, "occurrence", int(self.occurrence))


# TODO: I'm suspicious of this distinction between MutationSpec and ResolvedMutationSpec. We only really need it because
# the data we send to distributors doesn't include  start_/end_pos, and I wanted to make that clear. Am I being
# hoodwinked by type annotations? Should I just stop worrying and merge them?
@dataclasses.dataclass(frozen=True)
class ResolvedMutationSpec(MutationSpec):
    "A MutationSpec with the location of the mutation resolved."
    start_pos: Tuple[int, int]
    end_pos: Tuple[int, int]

    # pylint: disable=R0913
    def __post_init__(self):
        super().__post_init__()
        if self.start_pos[0] > self.end_pos[0]:
            raise ValueError("Start line must not be after end line")

        if self.start_pos[0] == self.end_pos[0]:
            if self.start_pos[1] >= self.end_pos[1]:
                raise ValueError("End position must come after start position.")


@dataclasses.dataclass(frozen=True)
class WorkItem:
    """A collection (possibly empty) of mutations to perform for a single test.

    This ability to perform more than one mutation for a single test run is how we support
    higher-order mutations.
    """

    job_id: str
    mutations: Tuple[ResolvedMutationSpec]

    @classmethod
    def single(cls, job_id, mutation: ResolvedMutationSpec):
        """Construct a WorkItem with a single mutation.

        Args:
            job_id: The ID of the job.
            mutation: The single mutation for the WorkItem.

        Returns:
            A new `WorkItem` instance.
        """
        return cls(job_id, (mutation,))
