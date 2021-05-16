"Implementation of the 'execute' command."
import logging
import os

from cosmic_ray.config import ConfigDict
from cosmic_ray.plugins import get_distributor
from cosmic_ray.progress import reports_progress

log = logging.getLogger(__name__)

_progress_messages = {}  # pylint: disable=invalid-name


def _update_progress(work_db):
    num_work_items = work_db.num_work_items
    pending = num_work_items - work_db.num_results
    total = num_work_items
    remaining = total - pending
    message = "{} out of {} completed".format(remaining, total)
    _progress_messages[work_db.name] = message


def _report_progress(stream):
    for db_name, progress_message in _progress_messages.items():
        session = os.path.splitext(db_name)[0]
        print("{session} : {progress_message}".format(session=session, progress_message=progress_message), file=stream)


@reports_progress(_report_progress)
def execute(work_db, config: ConfigDict):
    """Execute any pending work in the database `work_db`,
    recording the results.

    This looks for any work in `work_db` which has no results, schedules it to
    be executed, and records any results that arrive.
    """
    _update_progress(work_db)
    distributor = get_distributor(config.distributor_name)

    def on_task_complete(job_id, work_result):
        work_db.set_result(job_id, work_result)
        _update_progress(work_db)
        log.info("Job %s complete", job_id)

    log.info("Beginning execution")
    distributor(
        work_db.pending_work_items,
        config.test_command,
        config.timeout,
        config.distributor_config,
        on_task_complete=on_task_complete,
    )
    log.info("Execution finished")
