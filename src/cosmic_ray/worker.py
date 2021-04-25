"""Workers handle HTTP requests for mutation-and-test.

A worker is a simple web server that listens for requests to do a mutation-and-test. It runs the `cosmic-ray
mutate-and-test` command to actually do the work. It then responds with the JSON-serialized WorkResult.
"""

import logging

from aiohttp import web

from cosmic_ray.mutating import mutate_and_test
from pathlib import Path

log = logging.getLogger()


async def handle(request):
    args = await request.json()
    result = await mutate_and_test(
        module_path=Path(args["module_path"]),
        python_version=args["python_version"],
        operator_name=args["operator"],
        occurrence=args["occurrence"],
        test_command=args["test_command"],
        timeout=args["timeout"],
    )
    # TODO: Deal with exceptions. There generally won't be any, so we can just return an abnormal result if there it.

    return web.json_response(
        {
            "worker_outcome": result.worker_outcome.value,
            "output": result.output,
            "test_outcome": result.test_outcome.value if result.test_outcome is not None else None,
            "diff": result.diff,
        }
    )


def run(port=None, path=None):
    """Run the worker HTTP server.

    You must specify either `port` or `path`, but not both.

    Args:
        port: The TCP port on which to listen.
        path: Path to Unix domain socket on which to listen.
    """
    if port is None and path is None:
        raise ValueError("Worker requires either a port or domain socket path")
    app = web.Application()
    app.add_routes([web.post("/", handle)])
    web.run_app(app, port=port, path=path)
