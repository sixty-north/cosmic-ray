import os
import subprocess
import sys
from pathlib import Path

import pytest

from cosmic_ray.tools.filters import line_filter
from cosmic_ray.work_item import MutationSpec, WorkItem, WorkResult, WorkerOutcome

# Skip these tests when running in GitHub Actions where a proper git
# workspace isn't available in the test environment.
skip_in_ci = pytest.mark.xfail(
    os.environ.get("GITHUB_ACTIONS") == "true",
    reason=("This test fails on non-master branches in CI, so we ignore this problem for now."),
)


@skip_in_ci
def test_smoke_test_on_initialized_session(initialized_session, fast_tests_root):
    command = [
        sys.executable,
        "-m",
        "cosmic_ray.tools.filters.line_filter",
        str(initialized_session.session),
        "--config",
        str(initialized_session.config),
    ]

    subprocess.check_call(command, cwd=str(fast_tests_root))


@skip_in_ci
def test_smoke_test_on_execd_session(execd_session, fast_tests_root):
    command = [
        sys.executable,
        "-m",
        "cosmic_ray.tools.filters.line_filter",
        str(execd_session.session),
        "--config",
        str(execd_session.config),
    ]

    subprocess.check_call(command, cwd=str(fast_tests_root))


class FakeWorkDB:
    def __init__(self):
        self.results = []

    @property
    def pending_work_items(self):
        return [
            WorkItem.single(
                "id1",
                MutationSpec(
                    module_path=Path("math.py"),
                    operator_name="Op1",
                    occurrence=1,
                    start_pos=(2, 0),
                    end_pos=(2, 5),
                ),
            ),
            WorkItem.single(
                "id2",
                MutationSpec(
                    module_path=Path("math.py"),
                    operator_name="Op2",
                    occurrence=2,
                    start_pos=(10, 0),
                    end_pos=(10, 5),
                ),
            ),
            WorkItem.single(
                "id3",
                MutationSpec(
                    module_path=Path("util.py"),
                    operator_name="Op3",
                    occurrence=3,
                    start_pos=(3, 0),
                    end_pos=(3, 5),
                ),
            ),
            WorkItem.single(
                "id4",
                MutationSpec(
                    module_path=Path("util.py"),
                    operator_name="Op4",
                    occurrence=4,
                    start_pos=(12, 0),
                    end_pos=(12, 5),
                ),
            ),
            WorkItem.single(
                "id5",
                MutationSpec(
                    module_path=Path("other.py"),
                    operator_name="Op5",
                    occurrence=5,
                    start_pos=(1, 0),
                    end_pos=(1, 5),
                ),
            ),
        ]

    def set_multiple_results(self, job_ids, work_result: WorkResult):
        for job_id in job_ids:
            self.results.append((job_id, work_result.worker_outcome))
            

def test_line_filter_skips_items_outside_configured_ranges():
    data = FakeWorkDB()
    parsed_files = {
        Path("math.py"): [(1, 4)],
    }

    line_filter.LineFilter()._skip_filtered(data, parsed_files)

    assert data.results == [
        ("id2", WorkerOutcome.SKIPPED),
        ("id3", WorkerOutcome.SKIPPED),
        ("id4", WorkerOutcome.SKIPPED),
        ("id5", WorkerOutcome.SKIPPED),
    ]
    
    
def test_line_filter_skips_all_items_when_no_files_are_configured():
    data = FakeWorkDB()
    parsed_files = {}

    line_filter.LineFilter()._skip_filtered(data, parsed_files)

    assert data.results == [
        ("id1", WorkerOutcome.SKIPPED),
        ("id2", WorkerOutcome.SKIPPED),
        ("id3", WorkerOutcome.SKIPPED),
        ("id4", WorkerOutcome.SKIPPED),
        ("id5", WorkerOutcome.SKIPPED),
    ]


def test_line_filter_keeps_all_items_when_all_ranges_match():
    data = FakeWorkDB()
    parsed_files = {
        Path("math.py"): [(1, 20)],
        Path("util.py"): [(1, 20)],
        Path("other.py"): [(1, 5)],
    }

    line_filter.LineFilter()._skip_filtered(data, parsed_files)

    assert data.results == []

def test_line_filter_supports_multiple_ranges_for_same_file():
    data = FakeWorkDB()
    parsed_files = {
        Path("math.py"): [(1, 4), (10, 10)],
        Path("util.py"): [(3, 3), (12, 12)],
    }

    line_filter.LineFilter()._skip_filtered(data, parsed_files)

    assert data.results == [
        ("id5", WorkerOutcome.SKIPPED),
    ]

def test_line_filter_supports_multiple_files():
    data = FakeWorkDB()
    parsed_files = {
        Path("math.py"): [(1, 4)],
        Path("util.py"): [(1, 5)],
    }

    line_filter.LineFilter()._skip_filtered(data, parsed_files)

    assert data.results == [
        ("id2", WorkerOutcome.SKIPPED),
        ("id4", WorkerOutcome.SKIPPED),
        ("id5", WorkerOutcome.SKIPPED),
    ]

def test_ranges_overlap_returns_true_when_mutation_overlaps_range():
    result = line_filter.LineFilter()._ranges_overlap(3, 5, [(1, 4)])

    assert result is True


def test_ranges_overlap_returns_false_when_mutation_does_not_overlap_range():
    result = line_filter.LineFilter()._ranges_overlap(10, 12, [(1, 4)])

    assert result is False


def test_parse_line_specs_supports_single_lines_and_ranges():
    result = line_filter.LineFilter()._parse_line_specs(["2", "5-7"])

    assert result == [(2, 2), (5, 7)]


def test_parse_line_specs_ignores_invalid_entries():
    result = line_filter.LineFilter()._parse_line_specs(["2", "bad", "7-3", "5-6"])

    assert result == [(2, 2), (5, 6)]


def test_parse_line_files_resolves_paths_relative_to_module_path_directory():
    files = {
        "math.py": ["1-4"],
        "util.py": ["10"],
    }

    result = line_filter.LineFilter()._parse_line_files(files, "src")

    assert result == {
        Path("src") / "math.py": [(1, 4)],
        Path("src") / "util.py": [(10, 10)],
    }


def test_parse_line_files_supports_single_file_module_path_with_basename():
    files = {
        "my_math.py": ["2-4"],
    }

    result = line_filter.LineFilter()._parse_line_files(files, "src/my_math.py")

    assert result == {
        Path("src/my_math.py"): [(2, 4)],
    }


def test_parse_line_files_ignores_mismatched_file_for_single_file_module_path():
    files = {
        "other.py": ["1-3"],
    }

    result = line_filter.LineFilter()._parse_line_files(files, "src/my_math.py")

    assert result == {}