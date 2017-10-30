from cosmic_ray.plugins import get_execution_engine
from cosmic_ray.tasks import worker, celery
from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.work_record import WorkRecord


# TODO: These should be put into plugins. Callers of execute() should pass an
# executor.


def local_executor(timeout, pending_work, config):
    for work_record in pending_work:
        yield worker.worker_task(
            work_record,
            timeout,
            config)


class CeleryExecutor:  # pylint: disable=too-few-public-methods
    def __init__(self, purge_queue=True):
        self.purge_queue = purge_queue

    def __call__(self, timeout, pending_work, config):
        try:
            results = worker.execute_work_records(
                timeout,
                pending_work,
                config)

            for result in results:
                yield WorkRecord(result.get())
        finally:
            if self.purge_queue:
                celery.app.control.purge()


ENGINES = {
    'local': local_executor,
    'celery': CeleryExecutor()
}


def execute(db_name):
    """Execute any pending work in the database stored in `db_name`, recording the
results.

    This looks for any work in `db_name` which has no results, schedules it to
    be executed, and records any results that arrive.
    """

    with use_db(db_name, mode=WorkDB.Mode.open) as work_db:
        config, timeout = work_db.get_config()
        engine_config = config['execution-engine']
        executor = get_execution_engine(engine_config['name'])
        work_records = executor(timeout,
                                work_db.pending_work,
                                config)

        for work_record in work_records:
            work_db.update_work_record(work_record)
