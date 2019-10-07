from parso.tree import Node

from cosmic_ray.operators.operator import Operator
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkItem


class Interceptor:
    def __init__(self, work_db: WorkDB):
        self.work_db = work_db

    def set_config(self, config):
        pass

    def pre_scan_module_path(self, module_path) -> bool:
        return True

    def post_scan_module_path(self, module_path):
        pass

    def pre_add_work_item(self,
                          operator: Operator,
                          node: Node,
                          new_work_item: WorkItem) -> bool:
        return True

    def post_add_work_item(self,
                           operator: Operator,
                           node: Node,
                           new_work_item: WorkItem):
        pass

    def post_init(self):
        pass
