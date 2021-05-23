"Tool for printing reports on mutation testing sessions."

import click

from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.tools.survival_rate import kills_count, survival_rate


@click.command()
@click.option("--show-output/--no-show-output", default=False, help="Display output of test executions")
@click.option("--show-diff/--no-show-diff", default=False, help="Display diff of mutants")
@click.option("--show-pending/--no-show-pending", default=False, help="Display results for incomplete tasks")
@click.argument("session-file", type=click.Path(dir_okay=False, readable=True, exists=True))
def report(show_output, show_diff, show_pending, session_file):
    """Print a nicely formatted report of test results and some basic statistics."""

    with use_db(session_file, WorkDB.Mode.open) as db:
        for work_item, result in db.completed_work_items:
            display_work_item(work_item)

            print("worker outcome: {}, test outcome: {}".format(result.worker_outcome, result.test_outcome))

            if show_output:
                print("=== OUTPUT ===")
                print(result.output)
                print("==============")

            if show_diff:
                print("=== DIFF ===")
                print(result.diff)
                print("============")

        if show_pending:
            for work_item in db.pending_work_items:
                display_work_item(work_item)

        num_items = db.num_work_items
        num_complete = db.num_results

        print("total jobs: {}".format(num_items))

        if num_complete > 0:
            print("complete: {} ({:.2f}%)".format(num_complete, num_complete / num_items * 100))
            num_killed = kills_count(db)
            print("surviving mutants: {} ({:.2f}%)".format(num_complete - num_killed, survival_rate(db)))
        else:
            print("no jobs completed")


def display_work_item(work_item):
    print("[job-id] {}".format(work_item.job_id))
    for mutation in work_item.mutations:
        print("{} {} {}".format(mutation.module_path, mutation.operator_name, mutation.occurrence))


if __name__ == "__main__":
    report()  # no-qa: no-value-for-parameter