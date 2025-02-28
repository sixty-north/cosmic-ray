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


def _generate_mutations(module_paths, operator_cfgs) -> Iterable[MutationSpec]:
    """Generate all possible MutationSpecs for the given modules and operators.

    Args:
        module_paths: Paths to the modules to mutate
        operator_cfgs: Configurations for the operators

    Yields:
        MutationSpec objects describing each possible mutation

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
                yield MutationSpec(
                    module_path=str(module_path),
                    operator_name=operator_name,
                    operator_args=operator_args,
                    occurrence=occurrence,
                    start_pos=start_pos,
                    end_pos=end_pos,
                )


def _all_work_items(
    module_paths, operator_cfgs, mutation_order=1, specific_order=None, mutation_limit=None, disable_overlapping=True
) -> Iterable[WorkItem]:
    """Iterable of all WorkItems for the given inputs.

    Args:
        module_paths: Paths to the modules to mutate
        operator_cfgs: Configurations for the operators
        mutation_order: The order of mutations to create (how many mutations per work item)
        specific_order: If specified, only generate mutations of exactly this order
        mutation_limit: Optional limit to the number of work items to generate. If specified,
                        a random sample will be selected rather than generating all combinations.
        disable_overlapping: Whether to disable mutations that affect the same code location.
                            Defaults to True, which prevents multiple mutations at the same spot.

    Yields:
        WorkItem objects containing the mutations to apply

    Raises:
        TypeError: If an operator is provided with a parameterization it can't use.
    """
    import itertools
    import random

    # Generate all possible mutations
    all_mutations = list(_generate_mutations(module_paths, operator_cfgs))

    if mutation_order <= 1:
        # First-order mutants (traditional approach)
        work_items = []
        for mutation in all_mutations:
            work_items.append(WorkItem.single(job_id=uuid.uuid4().hex, mutation=mutation))

        # If a limit is set, randomly sample the work items
        if mutation_limit is not None and mutation_limit < len(work_items):
            log.info(f"Limiting mutations from {len(work_items)} to {mutation_limit}")
            work_items = random.sample(work_items, mutation_limit)

        yield from work_items
    else:
        # Higher-order mutants
        # We'll collect all work items first so we can count and limit them if needed
        work_items = []

        # Determine which orders to generate
        if specific_order is not None:
            # Only generate mutations of the specific order
            orders_to_generate = [specific_order]
            log.info(f"Generating only mutations of order {specific_order}")
        else:
            # Generate all orders up to the maximum
            orders_to_generate = range(1, mutation_order + 1)
            log.info(f"Generating mutations of orders 1 to {mutation_order}")

        # Generate combinations for each requested order
        for order in orders_to_generate:
            for mutation_combo in itertools.combinations(all_mutations, order):
                # Filter out combinations with overlapping mutations if enabled
                if disable_overlapping and order > 1:
                    # Check if any mutations in this combo affect the same location
                    locations = []
                    has_overlap = False

                    for mutation in mutation_combo:
                        # Location is identified by module path and position
                        location = (mutation.module_path, mutation.start_pos, mutation.end_pos)
                        if location in locations:
                            has_overlap = True
                            break
                        locations.append(location)

                    if has_overlap:
                        continue  # Skip this combination as it has overlapping mutations

                # Add valid combination to work items
                work_items.append(WorkItem(job_id=uuid.uuid4().hex, mutations=tuple(mutation_combo)))

        # If a limit is set, randomly sample from all generated work items
        total_items = len(work_items)
        if mutation_limit is not None and mutation_limit < total_items:
            log.info(f"Limiting mutations from {total_items} to {mutation_limit}")
            work_items = random.sample(work_items, mutation_limit)

        yield from work_items


def init(module_paths, work_db: WorkDB, operator_cfgs, config=None):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      module_paths: iterable of pathlib.Paths of modules to mutate.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      operator_cfgs: A dict mapping operator names to parameterization dicts.
      config: Optional configuration object containing mutation options.

    Raises:
        TypeError: Arguments provided for an operator are invalid.
    """
    # By default each operator will be parameterized with an empty dict.
    work_db.clear()

    # Get mutation options from config if provided
    mutation_order = config.mutation_order if config else 1
    specific_order = config.specific_order if config else None
    mutation_limit = config.mutation_limit if config else None
    disable_overlapping = config.disable_overlapping_mutations if config else True

    work_db.add_work_items(
        _all_work_items(
            module_paths, operator_cfgs, mutation_order, specific_order, mutation_limit, disable_overlapping
        )
    )
