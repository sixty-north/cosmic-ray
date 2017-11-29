"Implementation of the 'init' command."
import logging
import uuid

import cosmic_ray.modules
from cosmic_ray.parsing import get_ast
from cosmic_ray.plugins import get_interceptor, interceptor_names, get_operator
from cosmic_ray.util import get_col_offset, get_line_number
from cosmic_ray.work_item import WorkItem


log = logging.getLogger()


class WorkDBInitCore:
    """Operator core that initializes a WorkDB for a specific module and operator.

    The idea is to walk the AST looking for nodes that the operator can mutate.
    As they're found, `visit_mutation_site` is called and this core adds new
    WorkItems to the WorkDB. Use this core to populate a WorkDB by creating one
    for each operator-module pair and running it over the module's AST.
    """
    def __init__(self, module, op_name, work_db):
        self.module = module
        self.op_name = op_name
        self.work_db = work_db
        self.occurrence = 0

    def visit_mutation_site(self, node, _, count):
        """Adds work items to the WorkDB as mutatable nodes are found.
        """
        self.work_db.add_work_items(
            WorkItem(
                job_id=uuid.uuid4().hex,
                module=self.module.__name__,
                operator=self.op_name,
                occurrence=self.occurrence + c,
                filename=self.module.__file__,
                line_number=get_line_number(node),
                col_offset=get_col_offset(node))
            for c in range(count))

        self.occurrence += count

        return node


def init(modules,
         work_db,
         config,
         timeout):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      modules: iterable of module objects to be mutated.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      config: The configuration for the new session.
      timeout: The timeout to apply to the work in the session.
    """
    operators = cosmic_ray.plugins.operator_names()
    work_db.set_config(
        config=config,
        timeout=timeout)

    work_db.clear_work_items()

    for module in modules:
        for op_name in operators:
            core = WorkDBInitCore(module, op_name, work_db)
            operator = get_operator(op_name)(core)
            module_ast = get_ast(module)
            operator.visit(module_ast)

    apply_interceptors(work_db)


def apply_interceptors(work_db):
    """Apply each registered interceptor to the WorkDB."""
    for name in interceptor_names():
        interceptor = get_interceptor(name)
        interceptor(work_db)
