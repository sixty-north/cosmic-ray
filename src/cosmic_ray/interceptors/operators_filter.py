"""An interceptor to Filter out operators
"""
import re
import logging

from cosmic_ray.interceptors import Interceptor
from cosmic_ray.work_item import WorkerOutcome

log = logging.getLogger()


class OperatorsFilterInterceptor(Interceptor):

    def set_config(self, config):
        self.exclude_operators = config.get('exclude-operators')

    def post_init(self):
        """Mark as skipped all work item with filtered operator
        """

        re_exclude_operators = re.compile('|'.join('(:?%s)' % e for e in self.exclude_operators))

        for item in self.work_db.pending_work_items:
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

                self._add_work_result(
                    item,
                    output="Filtered operator",
                    worker_outcome=WorkerOutcome.SKIPPED,
                )
