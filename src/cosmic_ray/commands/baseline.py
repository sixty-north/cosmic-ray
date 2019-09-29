import logging

from cosmic_ray.plugins import get_execution_engine
from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import TestOutcome, WorkerOutcome, WorkItem

log = logging.getLogger()


def baseline(db_name):
    """Execute a baseline run.

    A baseline is exactly like normal mutation testing run - it uses all of the same machinery - except that it only
    uses one operator, "no op". This allows users to verify that their configuration works.
    """
    try:
        with use_db(db_name, mode=WorkDB.Mode.open) as work_db:
            config = work_db.get_config()
            engine = get_execution_engine(config.execution_engine_name)

            # Clone a real work-item and use the no-op operator on the clone.
            template = next(iter(work_db.work_items()))
            work_item = WorkItem(
                module_path=template.module_path,
                operator_name='core/NoOp',
                occurrence=0,
                start_pos=template.start_pos,
                end_pos=template.end_pos,
                job_id=template.job_id)

            log.info("Baseline starting")

            engine(
                (work_item,),
                config,
                on_task_complete=_on_task_complete)

            log.info("Baseline finished")

    except FileNotFoundError as exc:
        raise FileNotFoundError(
            str(exc).replace('Requested file', 'Corresponding database',
                             1)) from exc
    except StopIteration:
        raise ValueError('No work items in work-db')


def _on_task_complete(_job_id, work_result):
    if work_result.worker_outcome != WorkerOutcome.NORMAL:
        raise BaselineError('Worker outcome abnormal', work_result)
    elif work_result.test_output != TestOutcome.SURVIVED:
        raise BaselineError('Baseline run was killed', work_result)


class BaselineError(Exception):
    def __init__(self, msg, work_result):
        super().__init__(msg)
        self._work_result = work_result

    @property
    def work_result(self):
        return self._work_result

    def __repr__(self):
        return 'BaselineError("{}", work_result={})'.format(
            self.args[0],
            repr(self.work_result))
