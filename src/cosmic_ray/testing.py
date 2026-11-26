"Support for running tests in a subprocess."

import logging
import os
import shlex
import signal
import subprocess
import sys
import traceback

from cosmic_ray.config import ConfigValueError
from cosmic_ray.work_item import TestOutcome

log = logging.getLogger(__name__)

if sys.platform == "win32":
    from cosmic_ray.windows_job import CREATE_SUSPENDED, Job


def validate_memory_limit(memory_limit_mb):
    """Reject invalid or unsupported limits before any mutation is executed."""
    if memory_limit_mb is None:
        return
    if isinstance(memory_limit_mb, bool) or not isinstance(memory_limit_mb, int) or memory_limit_mb <= 0:
        raise ConfigValueError("memory-limit-mb must be a positive integer")
    if sys.platform not in ("linux", "win32"):
        raise ConfigValueError("memory-limit-mb is supported only on Linux and Windows; omit it on this platform")


def _limit_memory(memory_limit_mb):
    """A ``preexec_fn`` that caps the address space of the test process and its children (Linux)."""
    import resource  # pylint: disable=import-outside-toplevel

    limit = int(memory_limit_mb) * 2**20

    def apply():
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

    return apply


def _kill_process_group(proc):
    """Kill the whole process group led by `proc`, falling back to just `proc`.

    `os.killpg` is not available on all platforms, and the group may already be gone.
    """
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (AttributeError, OSError):
        proc.kill()


# We use an asyncio-subprocess-based approach here instead of a simple
# subprocess.run()-based approach because there are problems with timeouts and
# reading from stderr in subprocess.run. Since we have to be prepared for test
# processes that run longer than timeout (and, indeed, which run forever), the
# broken subprocess stuff simply doesn't work. So we do this, which seems to
# work on all platforms.


def run_tests(command, timeout, memory_limit_mb=None):
    """Run test command in a subprocess.

    If the command exits with status 0, then we assume that all tests passed. If
    it exits with any other code, we assume a test failed. If the call to launch
    the subprocess throws an exception, we consider the test 'incompetent'.

    Tests which time out are considered 'killed' as well.

    Args:
        command (str): The command to execute.
        timeout (number): The maximum number of seconds to allow the tests to run.
        memory_limit_mb (int): Optional cap, in MiB, on the memory of the test command and the processes it
            starts. On Windows it caps the whole process tree; on Linux each process. A test run that hits it fails,
            so the mutant counts as killed.

    Return: A tuple `(TestOutcome, output)` where the `output` is a string
        containing the output of the command.

    Raises:
        ConfigValueError: If the memory limit is invalid or unsupported.
    """
    validate_memory_limit(memory_limit_mb)
    log.info("Running test (timeout=%s): %s", timeout, command)

    # We want to avoid writing pyc files in case our changes happen too fast for Python to
    # notice them. If the timestamps between two changes are too small, Python won't recompile
    # the source.
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        # `start_new_session` puts the test command in its own process group so that a
        # timeout can kill the whole group. Without it only the immediate child is
        # killed, and any process it spawned keeps running unsupervised.
        # On Windows a job object plays the part of the process group: closing it kills every process the test
        # command started, and it carries the memory cap.
        job = Job(memory_limit_mb) if sys.platform == "win32" else None
        limit = _limit_memory(memory_limit_mb) if memory_limit_mb and job is None else None
        try:
            proc = subprocess.Popen(  # pylint: disable=R1732
                shlex.split(command),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                preexec_fn=limit,
                creationflags=CREATE_SUSPENDED if job else 0,
            )
            if job:
                try:
                    job.adopt(proc)
                except BaseException:
                    # Assignment may fail before the suspended child belongs to the job.
                    # Closing the job alone cannot terminate that child.
                    try:
                        proc.kill()
                        proc.wait()
                    finally:
                        proc.stdout.close()
                        proc.stderr.close()
                    raise
            try:
                stdout, _ = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                if job:
                    job.close()
                else:
                    _kill_process_group(proc)
                proc.communicate()
                return (TestOutcome.KILLED, "timeout")
        finally:
            if job:
                job.close()

        if proc.returncode != 0:
            return (TestOutcome.KILLED, stdout.decode("utf-8"))

        return (TestOutcome.SURVIVED, stdout.decode("utf-8"))

    except Exception:  # pylint: disable=W0703
        return (TestOutcome.INCOMPETENT, traceback.format_exc())
