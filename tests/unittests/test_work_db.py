"Tests for the WorkDB"

import pytest

from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import MutationSpec, WorkItem, WorkResult, WorkerOutcome
from cosmic_ray.work_item import TestOutcome as TOutcome  # We do this to prevent pytest from "collecting" TOutcome

# pylint: disable=W0621,C0111


@pytest.fixture
def work_db():
    with use_db(":memory:", WorkDB.Mode.create) as db:
        yield db


def test_empty_db_has_no_pending_jobs(work_db):
    assert not list(work_db.pending_work_items)


def test_find_pending_job(work_db):
    item = WorkItem.single("job_id", MutationSpec("path", "operator", 0, (0, 0), (0, 1)))
    work_db.add_work_item(item)
    pending = list(work_db.pending_work_items)
    assert pending == [item]


def test_jobs_with_results_are_not_pending(work_db):
    work_db.add_work_item(WorkItem.single("job_id", MutationSpec("path", "operator", 0, (0, 0), (0, 1))))
    work_db.set_result(
        "job_id",
        WorkResult(output="data", test_outcome=TOutcome.KILLED, worker_outcome=WorkerOutcome.NORMAL, diff="diff"),
    )
    assert not list(work_db.pending_work_items)


def test_set_result_throws_KeyError_if_no_matching_work_item(work_db):
    with pytest.raises(KeyError):
        work_db.set_result(
            "job_id",
            WorkResult(output="data", test_outcome=TOutcome.KILLED, worker_outcome=WorkerOutcome.NORMAL, diff="diff"),
        )


def test_set_multiple_results_works(work_db):
    work_db.add_work_item(WorkItem.single("job_id", MutationSpec("path", "operator", 0, (0, 0), (0, 1))))

    work_db.set_result(
        "job_id",
        WorkResult(
            output="first result", test_outcome=TOutcome.KILLED, worker_outcome=WorkerOutcome.NORMAL, diff="diff"
        ),
    )

    work_db.set_result(
        "job_id",
        WorkResult(
            output="second result", test_outcome=TOutcome.KILLED, worker_outcome=WorkerOutcome.NORMAL, diff="diff"
        ),
    )

    results = [r for job_id, r in work_db.results if job_id == "job_id"]
    assert len(results) == 1
    assert results[0].output == "second result"


def test_num_work_items(work_db):
    count = 10
    for idx in range(count):
        work_db.add_work_item(WorkItem.single(f"job_id_{idx}", MutationSpec("path", "operator", 0, (0, 0), (0, 1))))
    assert work_db.num_work_items == count


def test_clear_removes_work_items(work_db):
    for idx in range(10):
        work_db.add_work_item(WorkItem.single(f"job_id_{idx}", MutationSpec("path", "operator", 0, (0, 0), (0, 1))))
    work_db.clear()
    assert work_db.num_work_items == 0


def test_clear_work_items_removes_results(work_db):
    for idx in range(10):
        work_db.add_work_item(WorkItem.single(f"job_id_{idx}", MutationSpec("path", "operator", 0, (0, 0), (0, 1))))
        work_db.set_result(f"job_id_{idx}", WorkResult(WorkerOutcome.NORMAL))

    work_db.clear()
    assert work_db.num_results == 0


def test_work_items(work_db):
    original = [
        WorkItem.single(
            f"job_id_{idx}",
            MutationSpec(f"path_{idx}", f"operator_{idx}", idx, (idx, idx), (idx, idx + 1)),
        )
        for idx in range(10)
    ]
    for item in original:
        work_db.add_work_item(item)

    actual = list(work_db.work_items)

    assert actual == original


def test_results(work_db):
    for idx in range(10):
        work_db.add_work_item(
            WorkItem.single(
                f"job_id_{idx}",
                MutationSpec(f"path_{idx}", f"operator_{idx}", idx, (idx, idx), (idx, idx + 1)),
            )
        )

    original = [
        (
            f"job_id_{idx}",
            WorkResult(
                output=f"data_{idx}",
                test_outcome=TOutcome.KILLED,
                worker_outcome=WorkerOutcome.NORMAL,
                diff=f"diff_{idx}",
            ),
        )
        for idx in range(10)
    ]

    for result in original:
        work_db.set_result(*result)

    actual = list(work_db.results)

    assert actual == original


def test_new_work_items_are_pending(work_db):
    items = [
        WorkItem.single(
            f"job_id_{idx}",
            MutationSpec(f"path_{idx}", f"operator_{idx}", idx, (idx, idx), (idx, idx + 1)),
        )
        for idx in range(10)
    ]

    for idx, item in enumerate(items):
        assert sorted(list(work_db.pending_work_items), key=repr) == sorted(items[:idx], key=repr)
        work_db.add_work_item(item)


def test_adding_result_clears_pending(work_db):
    items = [
        WorkItem.single(
            f"job_id_{idx}",
            MutationSpec(f"path_{idx}", f"operator_{idx}", idx, (idx, idx), (idx, idx + 1)),
        )
        for idx in range(10)
    ]

    for item in items:
        work_db.add_work_item(item)

    for idx, item in enumerate(items):
        assert sorted(list(work_db.pending_work_items), key=repr) == sorted(items[idx:], key=repr)
        result = (
            f"job_id_{idx}",
            WorkResult(
                output=f"data_{idx}",
                test_outcome=TOutcome.KILLED,
                worker_outcome=WorkerOutcome.NORMAL,
                diff=f"diff_{idx}",
            ),
        )
        work_db.set_result(*result)


def test_adding_result_completes_work_item(work_db):
    items = [
        WorkItem.single(
            f"job_id_{idx}",
            MutationSpec(f"path_{idx}", f"operator_{idx}", idx, (idx, idx), (idx, idx + 1)),
        )
        for idx in range(10)
    ]

    for item in items:
        work_db.add_work_item(item)

    for idx, item in enumerate(items):
        assert [r[0] for r in work_db.completed_work_items] == items[:idx]
        result = (
            f"job_id_{idx}",
            WorkResult(
                output=f"data_{idx}",
                test_outcome=TOutcome.KILLED,
                worker_outcome=WorkerOutcome.NORMAL,
                diff=f"diff_{idx}",
            ),
        )
        work_db.set_result(*result)
