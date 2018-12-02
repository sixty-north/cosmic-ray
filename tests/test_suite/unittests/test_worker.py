from pathlib import Path
import sys

from cosmic_ray.operators import boolean_replacer
from cosmic_ray.work_item import WorkerOutcome, WorkResult
from cosmic_ray.worker import worker

from path_utils import excursion


def test_no_test_return_value(data_dir, python_version):
    with excursion(data_dir):
        result = worker(
            Path("a/b.py"), python_version, 'core/ReplaceTrueWithFalse', 100,
            'python -m unittest tests', 1000)
        expected = WorkResult(
            output=None,
            test_outcome=None,
            diff=None,
            worker_outcome=WorkerOutcome.NO_TEST)
        assert result == expected
