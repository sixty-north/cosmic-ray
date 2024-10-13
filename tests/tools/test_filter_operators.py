import subprocess
import sys

from cosmic_ray.tools.filters import operators_filter
from cosmic_ray.work_item import MutationSpec, WorkItem, WorkResult, WorkerOutcome


def test_smoke_test_on_initialized_session(initialized_session):
    command = [
        sys.executable,
        "-m",
        "cosmic_ray.tools.filters.operators_filter",
        str(initialized_session.session),
        str(initialized_session.config),
    ]

    subprocess.check_call(command, cwd=str(initialized_session.session.parent))


def test_smoke_test_on_execd_session(execd_session):
    command = [
        sys.executable,
        "-m",
        "cosmic_ray.tools.filters.operators_filter",
        str(execd_session.session),
        str(execd_session.config),
    ]

    subprocess.check_call(command, cwd=str(execd_session.session.parent))


class FakeWorkDB:
    def __init__(self):
        self.count = 0
        self.results = []

    def new_work_item(self, operator_name, job_id):
        self.count += 1
        return WorkItem.single(
            job_id,
            MutationSpec(
                module_path=f"{self.count}.py",
                operator_name=operator_name,
                occurrence=self.count,
                start_pos=(self.count, self.count),
                end_pos=(self.count + 1, self.count + 1),
            ),
        )

    @property
    def pending_work_items(self):
        return [
            self.new_work_item("Op1", "id1"),
            self.new_work_item("Op2", "id2"),
            self.new_work_item("Op3", "id3"),
            self.new_work_item("Op2", "id4"),
            self.new_work_item("Opregex1", "regex1"),
            self.new_work_item("Opregex2", "regex2"),
            self.new_work_item("Opregex3", "regex3"),
            self.new_work_item("Complex1", "regex4"),
            self.new_work_item("CompLex2", "regex5"),
        ]

    def set_result(self, job_id, work_result: WorkResult):
        self.results.append((job_id, work_result.worker_outcome))

    @property
    def expected_after_filter(self):
        return [
            ("id1", WorkerOutcome.SKIPPED),
            ("id2", WorkerOutcome.SKIPPED),
            ("id4", WorkerOutcome.SKIPPED),
            ("regex1", WorkerOutcome.SKIPPED),
            ("regex2", WorkerOutcome.SKIPPED),
            ("regex4", WorkerOutcome.SKIPPED),
        ]

    @property
    def expected_all_filtered(self):
        return [
            ("id1", WorkerOutcome.SKIPPED),
            ("id2", WorkerOutcome.SKIPPED),
            ("id3", WorkerOutcome.SKIPPED),
            ("id4", WorkerOutcome.SKIPPED),
            ("regex1", WorkerOutcome.SKIPPED),
            ("regex2", WorkerOutcome.SKIPPED),
            ("regex3", WorkerOutcome.SKIPPED),
            ("regex4", WorkerOutcome.SKIPPED),
            ("regex5", WorkerOutcome.SKIPPED),
        ]


def test_operators_filter():
    data = FakeWorkDB()
    exclude = ["Op1", "Op2", "Opregex[12]", r"(?:.[oO]m(?:p|P)lex).*"]
    operators_filter.OperatorsFilter()._skip_filtered(data, exclude)
    assert data.results == data.expected_after_filter


def test_operators_filter_empty_excludes():
    data = FakeWorkDB()
    exclude = []
    operators_filter.OperatorsFilter()._skip_filtered(data, exclude)
    assert data.results == []


def test_operators_filter_all_excluded():
    data = FakeWorkDB()
    exclude = [r"."]
    operators_filter.OperatorsFilter()._skip_filtered(data, exclude)
    assert data.results == data.expected_all_filtered
