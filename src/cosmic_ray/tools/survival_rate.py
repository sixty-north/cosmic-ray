"Tool for printing the survival rate in a session."

import math
import sys
import docopt

from cosmic_ray.work_db import use_db, WorkDB


def format_survival_rate():
    """cr-rate

Usage: cr-rate [--estimate] [--confidence <confidence_rate>] [--fail-over <max_value>] <session-file>

Calculate the survival rate of a session.

options:
    --estimate                     Print the lower bound, estimate and upper bound of
                                   survival rate
    --confidence <confidence_rate> Specify the confidence levels for estimates, 95 (%) by
                                   default. 80, 90, 95, 98, 99, 99.5, 99.8 and 99.9 are
                                   supported.
    --fail-over <max_value>        Exit with a non-zero code if the survival rate is
                                   larger than <max_value> or the calculated confidence
                                   interval is above the <max_value> (if --estimate is used).
                                   Specified as percentage.
"""
    arguments = docopt.docopt(
        format_survival_rate.__doc__, version='cr-rate 1.0')
    show_estimate = arguments['--estimate']
    confidence = arguments['--confidence']
    fail_over = arguments['--fail-over']

    # use integers as keys as equality is not well defined for floats
    # the values are z-values for Standard Normal Probabilities
    supp_z_scores = {800: 1.282,
                     900: 1.645,
                     950: 1.960,
                     980: 2.326,
                     990: 2.576,
                     995: 2.807,
                     998: 3.080,
                     999: 3.291}

    if not confidence:
        confidence = 95

    try:
        z_score = supp_z_scores[int(float(confidence)*10)]
    except KeyError:
        raise ValueError("Unsupported confidence interval: {0}"
                         .format(confidence))

    with use_db(arguments['<session-file>'], WorkDB.Mode.open) as db:
        rate = survival_rate(db)
        num_items = db.num_work_items
        num_complete = db.num_results

    if show_estimate:
        conf_int = math.sqrt(rate * (100-rate) / num_complete) \
                   * z_score * (1 - math.sqrt(num_complete / num_items))
        min_rate = rate - conf_int
        print('{:.2f} {:.2f} {:.2f}'
              .format(min_rate, rate, rate + conf_int))

    else:
        print('{:.2f}'.format(rate))
        min_rate = rate

    if fail_over and min_rate > float(fail_over):
        sys.exit(1)


def survival_rate(work_db):
    """Calcuate the survival rate for the results in a WorkDB.
    """
    kills = sum(r.is_killed for _, r in work_db.results)
    num_results = work_db.num_results

    if not num_results:
        return 0

    return (1 - kills / num_results) * 100
