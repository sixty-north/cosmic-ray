"""An filter that removes operators based on regular expressions.
"""
from argparse import Namespace
import logging
import re
import sys

from cosmic_ray.config import load_config
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkerOutcome, WorkResult
from cosmic_ray.tools.filters.filter_app import FilterApp

log = logging.getLogger()


class OperatorsFilter(FilterApp):
    "Implemenents the operators-filter."
    def description(self):
        return __doc__

    def _skip_filtered(self, work_db, exclude_operators):
        re_exclude_operators = re.compile('|'.join('(:?%s)' % e for e in exclude_operators))

        for item in work_db.pending_work_items:
            if re_exclude_operators.match(item.operator_name):
                log.info(
                    "operator skipping %s %s %s %s %s %s",
                    item.job_id,
                    item.operator_name,
                    item.occurrence,
                    item.module_path,
                    item.start_pos,
                    item.end_pos,
                )

                work_db.set_result(
                    item.job_id,
                    WorkResult(
                        output="Filtered operator",
                        worker_outcome=WorkerOutcome.SKIPPED,
                    ),
                )

    def filter(self, work_db: WorkDB, args: Namespace):
        """Mark as skipped all work item with filtered operator
        """

        if args.config is None:
            config = work_db.get_config()
        else:
            config = load_config(args.config)

        exclude_operators = config.sub('filters', 'operators-filter').get('exclude-operators', ())
        self._skip_filtered(work_db, exclude_operators)

    def add_args(self, parser):
        parser.add_argument('--config', help='Config file to use')


def main(argv=None):
    """Run the operators-filter with the specified command line arguments.
    """
    return OperatorsFilter().main(argv)


if __name__ == '__main__':
    sys.exit(main())
