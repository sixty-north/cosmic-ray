"Tool for printing the survival rate in a session."

import math
import sys

import click

from cosmic_ray.work_db import WorkDB, use_db

SUPPORTED_Z_SCORES = {800: 1.282, 900: 1.645, 950: 1.960, 980: 2.326, 990: 2.576, 995: 2.807, 998: 3.080, 999: 3.291}


@click.command()
@click.option(
    "--estimate/--no-estimate", default=False, help="Print the lower bound, estimate and upper bound of survival rate"
)
@click.option(
    "--confidence",
    type=click.Choice(sorted([str(z / 10) for z in SUPPORTED_Z_SCORES])),
    default=95,
    help="Specify the confidence levels for estimates",
)
@click.option(
    "--fail-over",
    type=click.FloatRange(0, 100),
    default=None,
    help="Exit with a non-zero code if the survival rate is larger than <max_value> or the calculated confidence interval is above the <max_value> (if --estimate is used).  Specified as percentage.",
)
@click.argument("session-file", type=click.Path(dir_okay=False, readable=True, exists=True))
def format_survival_rate(estimate, confidence, fail_over, session_file):
    """Calculate the survival rate of a session."""
    confidence = float(confidence)
    try:
        z_score = SUPPORTED_Z_SCORES[int(float(confidence) * 10)]
    except KeyError:
        raise ValueError("Unsupported confidence interval: {0}".format(confidence))

    with use_db(session_file, WorkDB.Mode.open) as db:
        rate = survival_rate(db)
        num_items = db.num_work_items
        num_complete = db.num_results

    if estimate:
        conf_int = math.sqrt(rate * (100 - rate) / num_complete) * z_score * (1 - math.sqrt(num_complete / num_items))
        min_rate = rate - conf_int
        print("{:.2f} {:.2f} {:.2f}".format(min_rate, rate, rate + conf_int))

    else:
        print("{:.2f}".format(rate))
        min_rate = rate

    if fail_over and min_rate > float(fail_over):
        sys.exit(1)


def kills_count(work_db):
    """Return the number of killed mutants."""
    return sum(r.is_killed for _, r in work_db.results)


def survival_rate(work_db):
    """Calculate the survival rate for the results in a WorkDB."""
    kills = kills_count(work_db)
    num_results = work_db.num_results

    if not num_results:
        return 0

    return (1 - kills / num_results) * 100
