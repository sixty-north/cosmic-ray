"Implementation of the 'init' command."
import logging
from typing import Iterable
import uuid
from cosmic_ray.ast import get_ast, ast_nodes
import cosmic_ray.modules
from cosmic_ray.work_item import ResolvedMutationSpec, WorkItem
from cosmic_ray.plugins import get_operator
from cosmic_ray.work_db import WorkDB

log = logging.getLogger()


def _all_work_items(module_paths, operator_cfgs) -> Iterable[WorkItem]:
    "Iterable of all WorkItems for the given inputs."

    for module_path in module_paths:
        module_ast = get_ast(module_path)

        for operator_cfg in operator_cfgs:
            operator_name = operator_cfg["name"]
            if "args" not in operator_cfg:
                operator_args = [{}]
            else:
                operator_args = operator_cfg["args"]

            for args in operator_args:
                try:
                    operator = get_operator(operator_name)(**args)
                except TypeError:
                    # Operator can't be loaded because it requires args, try next type
                    continue
                else:
                    positions = (
                        (start_pos, end_pos)
                        for node in ast_nodes(module_ast)
                        for start_pos, end_pos in operator.mutation_positions(node)
                    )

                    for occurrence, (start_pos, end_pos) in enumerate(positions):
                        mutation = ResolvedMutationSpec(
                            module_path=str(module_path),
                            operator_name=operator_name,
                            operator_args=args,
                            occurrence=occurrence,
                            start_pos=start_pos,
                            end_pos=end_pos,
                        )
                        yield WorkItem.single(job_id=uuid.uuid4().hex, mutation=mutation)


def init(module_paths, work_db: WorkDB, operators_cfgs=None):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      module_paths: iterable of pathlib.Paths of modules to mutate.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      operators_cfgs: A list of dictionaries representing operator configurations.
    """
    if not operators_cfgs:
        operators_cfgs = [{'name': name} for name in list(cosmic_ray.plugins.operator_names())]

    work_db.clear()
    work_db.add_work_items(_all_work_items(module_paths, operators_cfgs))
