from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.plugins import get_execution_engine


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
