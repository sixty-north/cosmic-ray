"Tests for worker."

import asyncio
from pathlib import Path

from cosmic_ray.work_item import MutationSpec, WorkerOutcome, WorkResult
from cosmic_ray.mutating import mutate_and_test


def test_no_test_return_value(path_utils, data_dir):
    with path_utils.excursion(data_dir):
        result = asyncio.get_event_loop().run_until_complete(
            mutate_and_test(
                [MutationSpec(Path("a/b.py"), "core/ReplaceTrueWithFalse", 100)],
                "python -m unittest tests",
                1000,
            )
        )

        expected = WorkResult(output=None, test_outcome=None, diff=None, worker_outcome=WorkerOutcome.NO_TEST)
        assert result == expected
