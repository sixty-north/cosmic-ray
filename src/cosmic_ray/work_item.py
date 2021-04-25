"""Classes for describing work and results.
"""
import dataclasses
import enum
import json
import pathlib
from typing import List, Optional
from pathlib import Path


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
    diff: Optional[List[str]] = None

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

    # def __eq__(self, rhs):
    #     return self.as_dict() == rhs.as_dict()

    # def __neq__(self, rhs):
    #     return not self == rhs

    # def __repr__(self):
    #     return "<WorkResult {test_outcome}/{worker_outcome}: '{output}'>".format(
    #         test_outcome=self._test_outcome, worker_outcome=self.worker_outcome, output=self.output
    #     )


@dataclasses.dataclass(frozen=True)
class WorkItem:
    """Description of the work for a single mutation and test run."""

    module_path: Path
    operator_name: str
    occurrence: int
    start_pos: int
    end_pos: int
    job_id: str

    # pylint: disable=R0913
    def __post_init__(self):
        if self.start_pos[0] > self.end_pos[0]:
            raise ValueError("Start line must not be after end line")

        if self.start_pos[0] == self.end_pos[0]:
            if self.start_pos[1] >= self.end_pos[1]:
                raise ValueError("End position must come after start position.")

        object.__setattr__(self, "module_path", pathlib.Path(self.module_path))
        object.__setattr__(self, "occurrence", int(self.occurrence))

    # def as_dict(self):
    #     """Get fields as a dict."""
    #     return {
    #         "module_path": str(self.module_path),
    #         "operator_name": self.operator_name,
    #         "occurrence": self.occurrence,
    #         "start_pos": self.start_pos,
    #         "end_pos": self.end_pos,
    #         "job_id": self.job_id,
    #     }

    # def __eq__(self, rhs):
    #     return self.as_dict() == rhs.as_dict()

    # def __neq__(self, rhs):
    #     return not self == rhs

    # def __repr__(self):
    #     return "<WorkItem {job_id}: ({start_pos}/{end_pos}) {occurrence} - {operator} ({module})>".format(
    #         job_id=self.job_id,
    #         start_pos=self.start_pos,
    #         end_pos=self.end_pos,
    #         occurrence=self.occurrence,
    #         operator=self.operator_name,
    #         module=self.module_path,
    #     )


class WorkItemJsonEncoder(json.JSONEncoder):
    "Custom JSON encoder for workitems and workresults."

    def default(self, o):  # pylint: disable=E0202
        if isinstance(o, WorkItem):
            return {"_type": "WorkItem", "values": o.as_dict()}

        if isinstance(o, WorkResult):
            return {"_type": "WorkResult", "values": o.as_dict()}

        return super().default(o)


class WorkItemJsonDecoder(json.JSONDecoder):
    "Custom JSON decoder for WorkItems and WorkResults."

    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self._decode_work_items)

    @staticmethod
    def _decode_work_items(obj):
        if (obj.get("_type") == "WorkItem") and ("values" in obj):
            values = obj["values"]
            return WorkItem(**values)

        if (obj.get("_type") == "WorkResult") and ("values" in obj):
            values = obj["values"]
            return WorkResult(**values)

        return obj
