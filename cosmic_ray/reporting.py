"""Functions for calculate certain kinds of reports.
"""

from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.worker import WorkerOutcome


def _print_item(work_item, full_report):
    data = work_item.data
    outcome = work_item.worker_outcome
    if outcome in {WorkerOutcome.NORMAL, WorkerOutcome.ABNORMAL, WorkerOutcome.EXCEPTION}:
        outcome = work_item.test_outcome
    ret_val = [
        'job ID {}:{}:{}'.format(
            work_item.job_id,
            outcome,
            work_item.module),
        'command: {}'.format(work_item.command_line or '')
    ]
    if outcome in {TestOutcome.KILLED, TestOutcome.INCOMPETENT} and not full_report:
        ret_val = []
    elif work_item.worker_outcome == WorkerOutcome.TIMEOUT:
        if full_report:
            ret_val.append("timeout: {:.3f} sec".format(data))
        else:
            ret_val = []
    elif work_item.worker_outcome == WorkerOutcome.SKIPPED and not full_report:
        ret_val = []
    elif work_item.worker_outcome in {WorkerOutcome.NORMAL,
                                      WorkerOutcome.EXCEPTION}:
        ret_val += data

        if work_item.diff is not None:
            ret_val += work_item.diff

    # for presentation purposes only
    if ret_val:
        ret_val.append('')

    return ret_val


def is_killed(record):
    """Determines if a WorkItem should be considered "killed".
    """
    if record.worker_outcome in {WorkerOutcome.TIMEOUT, WorkerOutcome.SKIPPED}:
        return True
    elif record.worker_outcome in {WorkerOutcome.ABNORMAL, WorkerOutcome.NORMAL}:
        if record.test_outcome == TestOutcome.KILLED:
            return True
        if record.test_outcome == TestOutcome.INCOMPETENT:
            return True
    return False


def create_report(records, show_pending, full_report=False):
    """Generate the lines of a simple report.

    Args:
      records: An iterable of `WorkItem`s.
      show_pending: Show output for records which are pending.
      full_report: Whether to report on mutants that were killed.
    """
    total_jobs = 0
    pending_jobs = 0
    kills = 0
    for item in records:
        total_jobs += 1
        if item.worker_outcome is None:
            pending_jobs += 1
        if is_killed(item):
            kills += 1
        if (item.worker_outcome is not None) or show_pending:
            yield from _print_item(item, full_report)

    completed_jobs = total_jobs - pending_jobs

    yield 'total jobs: {}'.format(total_jobs)

    if completed_jobs > 0:
        yield 'complete: {} ({:.2f}%)'.format(
            completed_jobs, completed_jobs / total_jobs * 100)
        yield 'survival rate: {:.2f}%'.format(
            (1 - kills / completed_jobs) * 100)
    else:
        yield 'no jobs completed'


def survival_rate(records):
    """Calcuate the survival rate for a series of WorkItems.
    """
    total_jobs = 0
    pending_jobs = 0
    kills = 0
    for item in records:
        total_jobs += 1
        if item.worker_outcome is None:
            pending_jobs += 1
        if is_killed(item):
            kills += 1

    completed_jobs = total_jobs - pending_jobs

    if not completed_jobs:
        rate = 0
    else:
        rate = (1 - kills / completed_jobs) * 100

    return rate
