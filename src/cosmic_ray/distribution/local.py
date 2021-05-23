"""Cosmic Ray distributor that runs tests sequentially and locally.

Enabling the distributor
========================

To use the local distributor, set ``cosmic-ray.distributor.name = "local"`` in your Cosmic Ray configuration:

.. code-block:: toml

    [cosmic-ray.distributor]
    name = "local"
"""

import asyncio
import logging

from cosmic_ray.distribution.distributor import Distributor
from cosmic_ray.mutating import mutate_and_test

log = logging.getLogger(__name__)


class LocalDistributor(Distributor):
    "The local distributor."

    def __call__(self, *args, **kwargs):
        asyncio.get_event_loop().run_until_complete(self._process(*args, **kwargs))

    async def _process(self, pending_work, test_command, timeout, _distributor_config, on_task_complete):
        for work_item in pending_work:
            result = await mutate_and_test(
                mutations=work_item.mutations,
                test_command=test_command,
                timeout=timeout,
            )
            on_task_complete(work_item.job_id, result)
