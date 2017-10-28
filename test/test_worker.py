from cosmic_ray.operators import zero_iteration_loop
from cosmic_ray.plugins import get_test_runner
from cosmic_ray.work_record import WorkRecord
from cosmic_ray.worker import worker, WorkerOutcome

from path_utils import DATA_DIR, excursion, extend_path


def test_no_test_return_value():
    with extend_path(DATA_DIR), excursion(DATA_DIR):
        test_runner = get_test_runner("unittest", ".")
        result = worker("a.b", zero_iteration_loop.ZeroIterationLoop,
                        100, test_runner)
        expected = WorkRecord(
            data=None,
            test_outcome=None,
            worker_outcome=WorkerOutcome.NO_TEST,
            diff=None,
            module=None,
            operator=None,
            occurrence=None,
            line_number=None,
            command_line=None,
            job_id=None)

        assert result == expected
