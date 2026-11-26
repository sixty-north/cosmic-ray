"""Cosmic Ray distributor that runs tests sequentially and locally.

Enabling the distributor
========================

To use the local distributor, set ``cosmic-ray.distributor.name = "local"`` in your Cosmic Ray configuration:

.. code-block:: toml

    [cosmic-ray.distributor]
    name = "local"

Limiting test memory
====================

A mutant can turn a loop into one that never ends while it keeps allocating. Set ``memory-limit-mb`` to cap the memory
of each test run; a run that hits the cap fails, so the mutant counts as killed:

.. code-block:: toml

    [cosmic-ray.distributor.local]
    memory-limit-mb = 2048

On Windows the cap covers the test command and every process it starts; on Linux it caps each process's address space.
The limit must be a positive integer. Memory limits are unsupported on macOS and other platforms; omit the option
there. Invalid or unsupported limits are rejected before running mutations, rather than counted as killed mutants.
"""

import logging

from cosmic_ray.distribution.distributor import Distributor
from cosmic_ray.mutating import mutate_and_test
from cosmic_ray.testing import validate_memory_limit

log = logging.getLogger(__name__)


class LocalDistributor(Distributor):
    "The local distributor."

    def __call__(self, pending_work, test_command, timeout, distributor_config, on_task_complete):
        memory_limit_mb = distributor_config.get("memory-limit-mb")
        validate_memory_limit(memory_limit_mb)
        for work_item in pending_work:
            result = mutate_and_test(
                mutations=work_item.mutations,
                test_command=test_command,
                timeout=timeout,
                memory_limit_mb=memory_limit_mb,
            )
            on_task_complete(work_item.job_id, result)
