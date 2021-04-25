"""Cosmic Ray distributor that runs tests sequentially and locally.

## Enabling the engine

To use the local distributor, set `cosmic-ray.distributor.name = "local"` in your Cosmic Ray configuration.

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

    async def _process(self, pending_work, python_version, test_command, timeout, engine_config, on_task_complete):
        for work_item in pending_work:
            result = await mutate_and_test(
                module_path=work_item.module_path,
                python_version=python_version,
                operator_name=work_item.operator_name,
                occurrence=work_item.occurrence,
                test_command=test_command,
                timeout=timeout,
            )
            on_task_complete(work_item.job_id, result)
