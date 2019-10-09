from parso.tree import Node

from cosmic_ray.operators.operator import Operator
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkItem, WorkerOutcome, WorkResult


class Interceptor:
    """
    Base class for all interceptors.

    """
    def __init__(self, work_db: WorkDB):
        self.work_db = work_db

    def set_config(self, config):
        """Allow interceptors get some configurations
        :param config: Sub part [interceptors.<class-name without "Interceptor">]
        """
        pass

    def pre_scan_module_path(self, module_path) -> bool:
        """Called when we start exploring a new file.
        Can be useful to handle some caches.
        :return True to allow this file exploration.
        """
        return True

    def post_scan_module_path(self, module_path):
        """Called when we end exploring a file.
        """
        pass

    def post_add_work_item(self,
                           operator: Operator,
                           node: Node,
                           new_work_item: WorkItem):
        """Called when a work_item id insrted in db.
        Here, you can add a skipped result for this work item.
        """
        pass

    def post_init(self):
        """Called when the ent of init process.
        Here, you can do any job in the database.
        """
        pass

    def _add_work_result(self, work_item,
                         output, worker_outcome: WorkerOutcome):
        self.work_db.set_result(
            work_item.job_id,
            WorkResult(
                output=output,
                test_outcome=None,
                diff=None,
                worker_outcome=worker_outcome,
            ),
        )
