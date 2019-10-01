"Implementation of the 'init' command."
import logging
import uuid

from parso.tree import Node

from cosmic_ray.ast import get_ast, Visitor, get_node_pragma_categories
import cosmic_ray.modules
from cosmic_ray.config import ConfigDict
from cosmic_ray.operators.operator import Operator
from cosmic_ray.plugins import get_interceptor, interceptor_names, get_operator
from cosmic_ray.work_item import WorkItem, WorkResult, WorkerOutcome
from cosmic_ray.work_db import WorkDB

log = logging.getLogger()


class WorkDBInitVisitor(Visitor):
    """An AST visitor that initializes a WorkDB for a specific module and operator.

    The idea is to walk the AST looking for nodes that the operator can mutate.
    As they're found, `activate` is called and this core adds new
    WorkItems to the WorkDB. Use this core to populate a WorkDB by creating one
    for each operator-module pair and running it over the module's AST.
    """

    def __init__(self, module_path, op_name, work_db, operator, pragma_cache):
        self.operator: Operator = operator
        self.module_path = module_path
        self.op_name = op_name
        self.work_db: WorkDB = work_db
        self.occurrence = 0
        self._pragma_cache = pragma_cache

    def visit(self, node: Node):
        for start, stop in self.operator.mutation_positions(node):
            job_id = self._record_work_item(start, stop)
            if self._have_excluding_pragma(node):
                self._record_skipped_result_item(job_id)
        return node

    def _have_excluding_pragma(self, node) -> bool:
        """
        Return true if node have à pragma declaration that exclude
        self.operator. For this it's look for 'no mutation' pragma en analyse
        sub category of this pragma declaration.

        It use cache mechanism of pragma information across visitors.
        """

        pragma_categories = self._pragma_cache.get(node, True)
        # pragma_categories can be (None, False, list):
        #   use True as guard

        if pragma_categories is True:
            pragma = get_node_pragma_categories(node)
            if pragma:
                pragma_categories = pragma.get('no mutate', False)
            else:
                pragma_categories = False
            # pragma_categories is None: Exclude all operator
            # pragma_categories is list: Exclude operators in the list
            # pragma_categories is False:
            #    guard indicate no pragma: no filter
            self._pragma_cache[node] = pragma_categories

        if pragma_categories is False:
            return False

        if pragma_categories is None:
            return True

        return self.operator.pragma_category_name in pragma_categories

    def _record_work_item(self, start_pos, end_pos):
        job_id = uuid.uuid4().hex
        self.work_db.add_work_item(
            WorkItem(
                job_id=job_id,
                module_path=str(self.module_path),
                operator_name=self.op_name,
                occurrence=self.occurrence,
                start_pos=start_pos,
                end_pos=end_pos))

        self.occurrence += 1
        return job_id

    def _record_skipped_result_item(self, job_id):
        self.work_db.set_result(
            job_id,
            WorkResult(
                worker_outcome=WorkerOutcome.SKIPPED,
                output="Skipped: pragma found",
            )
        )


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
    operator_names = cosmic_ray.plugins.operator_names()
    work_db.set_config(config=config)

    work_db.clear()

    for module_path in module_paths:
        module_ast = get_ast(
            module_path, python_version=config.python_version)

        pragma_cache = {}
        for op_name in operator_names:
            operator = get_operator(op_name)(config.python_version)
            visitor = WorkDBInitVisitor(module_path, op_name, work_db,
                                        operator, pragma_cache)
            visitor.walk(module_ast)

    apply_interceptors(work_db, config.sub('interceptors').get('enabled', ()))


def apply_interceptors(work_db, enabled_interceptors):
    """Apply each registered interceptor to the WorkDB."""
    names = (name for name in interceptor_names() if name in enabled_interceptors)
    for name in names:
        interceptor = get_interceptor(name)
        interceptor(work_db)
