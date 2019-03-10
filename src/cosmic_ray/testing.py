"Support for running tests in a subprocess."

import subprocess
import traceback

from cosmic_ray.work_item import TestOutcome


def run_tests(command, timeout=None):
    """Run test command in a subprocess.

    If the command exits with status 0, then we assume that all tests passed. If
    it exits with any other code, we assume a test failed. If the call to launch
    the subprocess throws an exception, we consider the test 'incompetent'.

    Tests which time out are considered 'incompetent' as well.

    Args:
        command (str): The command to execute.
        timeout (number): The maximum number of seconds to allow the tests to run.

    Return: A tuple `(TestOutcome, output)` where the `output` is a string
        containing the output of the command.
    """
    try:
        proc = subprocess.run(
            command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            universal_newlines=True,
            timeout=timeout,
        )

        return (TestOutcome.SURVIVED, proc.stdout)
    except subprocess.CalledProcessError as exc:
        return (TestOutcome.KILLED, exc.output)
    except Exception:  # pylint: disable=W0703
        return (TestOutcome.INCOMPETENT, traceback.format_exc())
