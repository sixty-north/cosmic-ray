"Implementation of the 'init' command."
import logging
import uuid

from parso.tree import Node

from cosmic_ray.ast import get_ast, Visitor
import cosmic_ray.modules
from cosmic_ray.config import ConfigDict
from cosmic_ray.interceptors import Interceptors
from cosmic_ray.operators.operator import Operator
from cosmic_ray.plugins import get_interceptor, interceptor_names, get_operator
from cosmic_ray.work_item import WorkItem
from cosmic_ray.work_db import WorkDB

log = logging.getLogger()


class WorkDBInitVisitor(Visitor):
    """An AST visitor that initializes a WorkDB for a specific module and operator.

    The idea is to walk the AST looking for nodes that the operator can mutate.
    As they're found, `activate` is called and this core adds new
    WorkItems to the WorkDB. Use this core to populate a WorkDB by creating one
    for each operator-module pair and running it over the module's AST.
    """

    def __init__(self, module_path, op_name, work_db, operator,
                 interceptors: Interceptors):
        self.operator = operator  # type: Operator
        self.module_path = module_path
        self.op_name = op_name
        self.work_db = work_db  # type: WorkDB
        self.occurrence = 0
        self._interceptors = interceptors

    def visit(self, node: Node):
        for start_stop in self.operator.mutation_positions(node):
            if len(start_stop) == 2:
                (start, stop), target_node = start_stop, node
            else:
                start, stop, target_node = start_stop

            self._record_work_item(target_node, start, stop)
        return node

    def _record_work_item(self, node, start_pos, end_pos):
        work_item = WorkItem(
            job_id=uuid.uuid4().hex,
            module_path=str(self.module_path),
            operator_name=self.op_name,
            occurrence=self.occurrence,
            start_pos=start_pos,
            end_pos=end_pos,
        )

        if self._interceptors.pre_add_work_item(self.operator,
                                                node, work_item):
            self.work_db.add_work_item(work_item)
            self._interceptors.post_add_work_item(self.operator,
                                                  node, work_item)
            self.occurrence += 1


def init(module_paths, work_db: WorkDB, config: ConfigDict):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      module_paths: iterable of pathlib.Paths of modules to mutate.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      config: The configuration for the new session.
    """

    operator_names = list(cosmic_ray.plugins.operator_names())

    work_db.set_config(config=config)

    enabled_interceptors = config.sub('interceptors').get('enabled', ())
    interceptors = [get_interceptor(name)(work_db)
                    for name in interceptor_names()
                    if name in enabled_interceptors]
    interceptors = Interceptors(interceptors, config.get('interceptors', {}))

    work_db.clear()

    for module_path in module_paths:
        module_ast = get_ast(module_path, python_version=config.python_version)
        visit_module(work_db, interceptors, module_path, module_ast,
                     operator_names, config)

    interceptors.post_init()


def visit_module(work_db, interceptors, module_path, module_ast,
                 operator_names, config):
    if interceptors.pre_scan_module_path(module_path):

        for op_name in operator_names:
            operator = get_operator(op_name)(config.python_version)
            visitor = WorkDBInitVisitor(module_path, op_name, work_db,
                                        operator, interceptors)
            visitor.walk(module_ast)

        interceptors.post_scan_module_path(module_path)
