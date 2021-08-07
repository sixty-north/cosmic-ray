"""An filter that removes operators based on regular expressions.
"""
import logging
import re
import sys
from argparse import ArgumentParser, Namespace

from cosmic_ray.config import load_config
from cosmic_ray.tools.filters.filter_app import FilterApp
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkerOutcome, WorkResult

log = logging.getLogger()


class OperatorsFilter(FilterApp):
    "Implemenents the operators-filter."

    def description(self):
        return __doc__

    def _skip_filtered(self, work_db, exclude_operators):
        if not exclude_operators:
            return

        re_exclude_operators = re.compile("|".join("(:?%s)" % e for e in exclude_operators))

        for item in work_db.pending_work_items:
            for mutation in item.mutations:
                if re_exclude_operators.match(mutation.operator_name):
                    log.info(
                        "operator skipping %s %s %s %s %s %s",
                        item.job_id,
                        mutation.operator_name,
                        mutation.occurrence,
                        mutation.module_path,
                        mutation.start_pos,
                        mutation.end_pos,
                    )

                    work_db.set_result(
                        item.job_id,
                        WorkResult(
                            output="Filtered operator",
                            worker_outcome=WorkerOutcome.SKIPPED,
                        ),
                    )

                    break

    def filter(self, work_db: WorkDB, args: Namespace):
        """Mark as skipped all work item with filtered operator"""

        config = load_config(args.config)

        exclude_operators = config.sub("filters", "operators-filter").get("exclude-operators", ())
        self._skip_filtered(work_db, exclude_operators)

    def add_args(self, parser: ArgumentParser):
        parser.add_argument("config", help="Config file to use")


def main(argv=None):
    """Run the operators-filter with the specified command line arguments."""
    return OperatorsFilter().main(argv)


if __name__ == "__main__":
    sys.exit(main())
