"Tool for printing the survival rate in a session."

import math
import docopt

from cosmic_ray.work_db import use_db, WorkDB


def format_survival_rate():
    """cr-rate

    Usage: cr-rate --estimate <session-file>

    Calculate the survival rate of a session.

    options:
        --estimate    Print the lower bound, estimate and upper bound of
                      survival rate
    """
    arguments = docopt.docopt(
        format_survival_rate.__doc__, version='cr-rate 1.0')
    show_estimate = arguments['--estimate']
    z_score = 1.96  # for 95% confidence interval

    with use_db(arguments['<session-file>'], WorkDB.Mode.open) as db:
        rate = survival_rate(db)
        num_items = db.num_work_items
        num_complete = db.num_results

    if show_estimate:
        conf_int = math.sqrt(rate * (100-rate) / num_complete) \
                   * z_score * (1 - math.sqrt(num_complete / num_items))
        print('{:.2f} {:.2f} {:.2f}'
              .format(rate-conf_int, rate, rate+conf_int))
    else:
        print('{:.2f}'.format(rate))


def survival_rate(work_db):
    """Calcuate the survival rate for the results in a WorkDB.
    """
    kills = sum(r.is_killed for _, r in work_db.results)
    num_results = work_db.num_results

    if not num_results:
        return 0

    return (1 - kills / num_results) * 100
