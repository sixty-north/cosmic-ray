from cosmic_ray.config import get_db_name
import cosmic_ray.tasks.celery
import cosmic_ray.tasks.worker
from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.work_record import WorkRecord

# TODO: These should be put into plugins. Callers of execute() should pass an
# executor.


def local_executor(timeout, pending_work, config):
    for work_record in pending_work:
        yield cosmic_ray.tasks.worker.worker_task(
            work_record,
            timeout,
            config)


class CeleryExecutor:
    def __init__(self, purge_queue=True):
        self.purge_queue = purge_queue

    def __call__(self, timeout, pending_work, config):
        try:
            results = cosmic_ray.tasks.worker.execute_work_records(
                timeout,
                pending_work,
                config)

            for r in results:
                yield WorkRecord(r.get())
        finally:
            if self.purge_queue:
                cosmic_ray.tasks.celery.app.control.purge()


ENGINES = {
    'local': local_executor,
    'celery': CeleryExecutor()
}


def execute(config):
    """Execute any pending work in `work_db`, recording the results.

    This looks for any work in `work_db` which has no results, schedules to be
    executed, and records any results that arrive.

    If `dist` is `True` then this uses Celery to distribute tasks to remote
    workers; of course you need to make sure that these are running if you want
    tests to actually run! If `dist` is `False` then all tests will be run
    locally.
    """

    db_name = get_db_name(config['session'])
    engine_config = config['execution-engine']
    executor = ENGINES[engine_config['name']]

    with use_db(db_name, mode=WorkDB.Mode.open) as work_db:
        test_runner, test_args, timeout = work_db.get_work_parameters()
        work_records = executor(timeout,
                                work_db.pending_work,
                                config)

        for work_record in work_records:
            work_db.update_work_record(work_record)
