"Support for running tests in a subprocess."

import asyncio
import os
import sys
import traceback

from cosmic_ray.work_item import TestOutcome

# We use an asyncio-subprocess-based approach here instead of a simple
# subprocess.run()-based approach because there are problems with timeouts and
# reading from stderr in subprocess.run. Since we have to be prepared for test
# processes that run longer than timeout (and, indeed, which run forever), the
# broken subprocess stuff simply doesn't work. So we do this, which seesm to
# work on all platforms.


async def _run_tests(command, timeout):
    # We want to avoid writing pyc files in case our changes happen too fast for Python to
    # notice them. If the timestamps between two changes are too small, Python won't recompile
    # the source.
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env)
    except Exception:  # pylint: disable=W0703
        return (TestOutcome.INCOMPETENT, traceback.format_exc())

    try:
        outs, errs = await asyncio.wait_for(proc.communicate(), timeout)

        assert proc.returncode is not None

        if proc.returncode == 0:
            return (TestOutcome.SURVIVED, outs.decode('utf-8'))
        else:
            return (TestOutcome.KILLED, outs.decode('utf-8'))

    except asyncio.TimeoutError:
        proc.terminate()
        return (TestOutcome.KILLED, 'timeout')
        
    except Exception:  # pylint: disable=W0703
        proc.terminate()
        return (TestOutcome.INCOMPETENT, traceback.format_exc())

    finally:
        await proc.wait()


def run_tests(command, timeout=None):
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

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsProactorEventLoopPolicy())

    result = asyncio.get_event_loop().run_until_complete(
        _run_tests(command, timeout))
    return result
