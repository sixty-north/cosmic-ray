"Implementation of the 'execute' command."
import os

from cosmic_ray.progress import reports_progress
from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.plugins import get_execution_engine


_progress_messages = {}  # pylint: disable=invalid-name


def _update_progress(work_db):
    pending = work_db.num_pending_work_items
    total = work_db.num_work_items
    remaining = total - pending
    message = "{} out of {} completed".format(remaining, total)
    _progress_messages[work_db.name] = message


def _report_progress(stream):
    for db_name, progress_message in _progress_messages.items():
        session = os.path.splitext(db_name)[0]
        print("{session} : {progress_message}"
              .format(session=session,
                      progress_message=progress_message),
              file=stream)


@reports_progress(_report_progress)
def execute(db_name):
    """Execute any pending work in the database stored in `db_name`,
    recording the results.

    This looks for any work in `db_name` which has no results, schedules it to
    be executed, and records any results that arrive.
    """
    try:
        with use_db(db_name, mode=WorkDB.Mode.open) as work_db:
            _update_progress(work_db)
            config, timeout = work_db.get_config()
            engine_config = config['execution-engine']
            executor = get_execution_engine(engine_config['name'])
            work_items = executor(timeout,
                                  work_db.pending_work_items,
                                  config)

            for work_item in work_items:
                work_db.update_work_item(work_item)
                _update_progress(work_db)
    except FileNotFoundError as exc:
        raise FileNotFoundError(str(exc).replace(
            'Requested file', 'Corresponding database', 1)) from exc
