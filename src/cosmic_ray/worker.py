"""Workers handle HTTP requests for mutation-and-test.

A worker is a simple web server that listens for requests to do a mutation-and-test. It runs the `cosmic-ray
mutate-and-test` command to actually do the work. It then responds with the JSON-serialized WorkResult.
"""

import logging
import asyncio
import json


from aiohttp import web

from cosmic_ray.work_item import WorkResult, WorkerOutcome, TestOutcome

log = logging.getLogger()


async def handle(request):
    args = await request.json()
    cmd = [
        "-m",
        "cosmic_ray.cli",
        "mutate-and-test",
        args["module_path"],
        args["operator"],
        str(args["occurrence"]),
        args["python_version"],
        args["test_command"],
    ]
    proc = await asyncio.create_subprocess_exec(
        "python", *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        # TODO: error response if stdout can't be deserialized.
        return web.json_response(json.loads(stdout))
    else:
        output = f"[STDOUT]\n{stdout}\n\n[STDERR]{stderr}"
        return web.json_response(
            WorkResult(
                worker_outcome=WorkerOutcome.ABNORMAL, output=output, test_outcome=TestOutcome.INCOMPETENT
            ).as_dict()
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
