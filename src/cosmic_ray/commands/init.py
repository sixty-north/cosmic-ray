"Implementation of the 'init' command."

import logging
import uuid
from collections.abc import Iterable

import cosmic_ray.modules
import cosmic_ray.plugins
from cosmic_ray.ast import ast_nodes, get_ast_from_path
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import MutationSpec, WorkItem

log = logging.getLogger()


def _operators(operator_cfgs):
    """Find all Operator instances that should be used for the session.

    Args:
        operator_cfgs (Mapping[str, Iterable[Mapping[str, Any]]]): Mapping
            of operator names to arguments sets for that operator. Each
            argument set for an operator will result in an instance of the
            operator.

    Yields:
        operators: tuples of (operator name, argument dict, operator instance).

    Raises:
        TypeError: The arguments supplied to an operator are invalid.
    """
    # TODO: Can/should we check for operator arguments which don't correspond to
    # *any* known operator?

    for operator_name in cosmic_ray.plugins.operator_names():
        operator_class = cosmic_ray.plugins.get_operator(operator_name)
        if not operator_class.arguments():
            if operator_name in operator_cfgs:
                raise TypeError(f"Arguments provided for operator {operator_name} which accepts no arguments")

            yield operator_name, {}, operator_class()
        else:
            for operator_args in operator_cfgs.get(operator_name, ()):
                yield operator_name, operator_args, operator_class(**operator_args)


def _all_work_items(module_paths, operator_cfgs) -> Iterable[WorkItem]:
    """Iterable of all WorkItems for the given inputs.

    Raises:
        TypeError: If an operator is provided with a parameterization it can't use.
    """

    for module_path in module_paths:
        module_ast = get_ast_from_path(module_path)

        for operator_name, operator_args, operator in _operators(operator_cfgs):
            positions = (
                (start_pos, end_pos)
                for node in ast_nodes(module_ast)
                for start_pos, end_pos in operator.mutation_positions(node)
            )

            for occurrence, (start_pos, end_pos) in enumerate(positions):
                mutation = MutationSpec(
                    module_path=str(module_path),
                    operator_name=operator_name,
                    operator_args=operator_args,
                    occurrence=occurrence,
                    start_pos=start_pos,
                    end_pos=end_pos,
                )
                yield WorkItem.single(job_id=uuid.uuid4().hex, mutation=mutation)


def init(module_paths, work_db: WorkDB, operator_cfgs):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      module_paths: iterable of pathlib.Paths of modules to mutate.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      operator_cfgs: A dict mapping operator names to parameterization dicts.

    Raises:
        TypeError: Arguments provided for an operator are invalid.
    """
    # By default each operator will be parameterized with an empty dict.
    work_db.clear()
    work_db.add_work_items(_all_work_items(module_paths, operator_cfgs))
