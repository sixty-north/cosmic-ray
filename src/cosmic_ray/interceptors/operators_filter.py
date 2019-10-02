"""An interceptor to Filter out operators
"""
import re
import logging

from cosmic_ray.config import ConfigDict
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkerOutcome, WorkResult

log = logging.getLogger()


def intercept(work_db: WorkDB, config: ConfigDict):
    """Mark as skipped all work item with filtered operator
    """

    exclude_operators = config.get('exclude-operators')
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
