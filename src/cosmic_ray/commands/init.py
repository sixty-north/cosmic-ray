"Implementation of the 'init' command."
import logging
import uuid

from cosmic_ray.ast import get_ast, Visitor
import cosmic_ray.modules
from cosmic_ray.plugins import get_interceptor, interceptor_names, get_operator
from cosmic_ray.work_item import WorkItem

log = logging.getLogger()


class WorkDBInitVisitor(Visitor):
    """An AST visitor that initializes a WorkDB for a specific module and operator.

    The idea is to walk the AST looking for nodes that the operator can mutate.
    As they're found, `activate` is called and this core adds new
    WorkItems to the WorkDB. Use this core to populate a WorkDB by creating one
    for each operator-module pair and running it over the module's AST.
    """

    def __init__(self, module_path, op_name, work_db, operator):
        self.operator = operator
        self.module_path = module_path
        self.op_name = op_name
        self.work_db = work_db
        self.occurrence = 0

    def visit(self, node):
        for start, stop in self.operator.mutation_positions(node):
            self._record_work_item(start, stop)
        return node

    def _record_work_item(self, start_pos, end_pos):
        self.work_db.add_work_item(
            WorkItem(
                job_id=uuid.uuid4().hex,
                module_path=str(self.module_path),
                operator_name=self.op_name,
                occurrence=self.occurrence,
                start_pos=start_pos,
                end_pos=end_pos))

        self.occurrence += 1


def init(module_paths, work_db, config):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      module_paths: iterable of pathlib.Paths of modules to mutate.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      config: The configuration for the new session.
    """
    operator_names = cosmic_ray.plugins.operator_names()
    work_db.set_config(config=config)

    work_db.clear()

    for module_path in module_paths:
        module_ast = get_ast(
            module_path, python_version=config.python_version)

        for op_name in operator_names:
            operator = get_operator(op_name)(config.python_version)
            visitor = WorkDBInitVisitor(module_path, op_name, work_db,
                                        operator)
            visitor.walk(module_ast)

    apply_interceptors(work_db, config.sub('interceptors').get('enabled', ()))


def apply_interceptors(work_db, enabled_interceptors):
    """Apply each registered interceptor to the WorkDB."""
    names = (name for name in interceptor_names() if name in enabled_interceptors)
    for name in names:
        interceptor = get_interceptor(name)
        interceptor(work_db)
