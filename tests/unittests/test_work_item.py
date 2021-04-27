from pathlib import Path
from cosmic_ray.work_item import WorkResult, WorkItem, TestOutcome, WorkerOutcome


class TestWorkResult:
    def test_repr(self):
        result = WorkResult(WorkerOutcome.NORMAL)
        repr(result)  # Just make sure it doesn't throw.


class TestWorkItem:
    def test_repr(self):
        item = WorkItem(
            module_path=Path('.'),
            operator_name='core/NoOp',
            occurrence=0,
            start_pos=(1, 1),
            end_pos=(1, 2),
            job_id='1')
        repr(item)  # Just make sure it doesn't throw.
