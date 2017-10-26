import logging
import uuid

import cosmic_ray.modules
from cosmic_ray.work_record import WorkRecord

LOG = logging.getLogger()


def init(modules,
         work_db,
         config,
         timeout):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      modules: iterable of module names to be mutated.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      config: The configuration for the new session.
      timeout: The timeout to apply to the work in the session.
    """
    operators = cosmic_ray.plugins.operator_names()
    counts = cosmic_ray.counting.count_mutants(modules, operators)
    work_db.set_config(
        config=config,
        timeout=timeout)

    work_db.clear_work_records()

    work_db.add_work_records(
        WorkRecord(
            job_id=uuid.uuid4().hex,
            module=module.__name__,
            operator=opname,
            occurrence=occurrence)
        for module, ops in counts.items()
        for opname, count in ops.items()
        for occurrence in range(count))
