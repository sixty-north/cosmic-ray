"""An filter that removes operators based on regular expressions.
"""
import logging
import re
import sys
from typing import Dict

from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkerOutcome, WorkResult
from cosmic_ray.tools.filters.filter_app import FilterApp

log = logging.getLogger()


class OperatorsFilter(FilterApp):
    def description(self):
        return __doc__

    def filter(self, work_db: WorkDB, config: Dict):
        """Mark as skipped all work item with filtered operator
        """

        exclude_operators = config.get('exclude-operators')
        if exclude_operators is None:
            return

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

    def add_args(self, parser):
        parser.add_argument('--config', help='Config file to use')


def main(argv=None):
    return OperatorsFilter().main(argv)


if __name__ == '__main__':
    sys.exit(main())
