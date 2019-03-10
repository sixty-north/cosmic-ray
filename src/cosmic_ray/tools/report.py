"Tool for printing reports on mutation testing sessions."

import docopt

from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.tools.survival_rate import survival_rate


def report():
    """cr-report

Usage: cr-report [--show-output] [--show-diff] [--show-pending] <session-file>

Print a nicely formatted report of test results and some basic statistics.

options:
    --show-output   Display output of test executions
    --show-diff     Display diff of mutants
    --show-pending  Display results for incomplete tasks
"""

    arguments = docopt.docopt(report.__doc__, version='cr-format 0.1')
    show_pending = arguments['--show-pending']
    show_output = arguments['--show-output']
    show_diff = arguments['--show-diff']

    with use_db(arguments['<session-file>'], WorkDB.Mode.open) as db:
        for work_item, result in db.completed_work_items:
            print('{} {} {} {}'.format(work_item.job_id, work_item.module_path,
                                       work_item.operator_name,
                                       work_item.occurrence))

            print('worker outcome: {}, test outcome: {}'.format(
                result.worker_outcome, result.test_outcome))

            if show_output:
                print('=== OUTPUT ===')
                print(result.output)
                print('==============')

            if show_diff:
                print('=== DIFF ===')
                print(result.diff)
                print('============')

        if show_pending:
            for work_item in db.pending_work_items:
                print('{} {} {} {}'.format(
                    work_item.job_id, work_item.module_path,
                    work_item.operator_name, work_item.occurrence))

        num_items = db.num_work_items
        num_complete = db.num_results

        print('total jobs: {}'.format(num_items))

        if num_complete > 0:
            print('complete: {} ({:.2f}%)'.format(
                num_complete, num_complete / num_items * 100))
            print('survival rate: {:.2f}%'.format(survival_rate(db)))
        else:
            print('no jobs completed')
