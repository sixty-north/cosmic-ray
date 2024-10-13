"Support for running tests in a subprocess."

import logging
import os
import shlex
import subprocess
import traceback

from cosmic_ray.work_item import TestOutcome

log = logging.getLogger(__name__)

# We use an asyncio-subprocess-based approach here instead of a simple
# subprocess.run()-based approach because there are problems with timeouts and
# reading from stderr in subprocess.run. Since we have to be prepared for test
# processes that run longer than timeout (and, indeed, which run forever), the
# broken subprocess stuff simply doesn't work. So we do this, which seems to
# work on all platforms.


def run_tests(command, timeout):
    """Run test command in a subprocess.

    If the command exits with status 0, then we assume that all tests passed. If
    it exits with any other code, we assume a test failed. If the call to launch
    the subprocess throws an exception, we consider the test 'incompetent'.

    Tests which time out are considered 'killed' as well.

    Args:
        command (str): The command to execute.
        timeout (number): The maximum number of seconds to allow the tests to run.

    Return: A tuple `(TestOutcome, output)` where the `output` is a string
        containing the output of the command.
    """
    log.info("Running test (timeout=%s): %s", timeout, command)

    # We want to avoid writing pyc files in case our changes happen too fast for Python to
    # notice them. If the timestamps between two changes are too small, Python won't recompile
    # the source.
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        proc = subprocess.run(shlex.split(command), check=True, env=env, timeout=timeout, capture_output=True)
        assert proc.returncode == 0
        return (TestOutcome.SURVIVED, proc.stdout.decode("utf-8"))

    except subprocess.CalledProcessError as err:
        return (TestOutcome.KILLED, err.output.decode("utf-8"))

    except subprocess.TimeoutExpired:
        return (TestOutcome.KILLED, "timeout")

    except Exception:  # pylint: disable=W0703
        return (TestOutcome.INCOMPETENT, traceback.format_exc())
