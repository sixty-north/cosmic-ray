"Tests for worker."

from pathlib import Path

from cosmic_ray.work_item import WorkerOutcome, WorkResult
from cosmic_ray.mutating import mutate_and_test


def test_no_test_return_value(path_utils, data_dir, python_version):
    with path_utils.excursion(data_dir):
        result = mutate_and_test(
            Path("a/b.py"), python_version, 'core/ReplaceTrueWithFalse', 100,
            'python -m unittest tests', 1000)
        expected = WorkResult(
            output=None,
            test_outcome=None,
            diff=None,
            worker_outcome=WorkerOutcome.NO_TEST)
        assert result == expected
