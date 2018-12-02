"""Management of progress reporting.

The design of this subsystem is such that progress reporting is
decoupled from updating the current progress. This allows for
progress reporting functions which can be invoked from another
context, such as a SIGINFO signal handler.

As such, reporter callables are responsible only for displaying
current progress, and must be capable of retrieving the latest
progress state from elsewhere when invoked. This may be global state
or reached through references that the reporter callable was
constructed with.  Typically the latest progress state will be
updated by the routine whose progress is being monitored.

To report the current progress invoke report_progress().

To manage installation and deinstallation of progress reporting
functions use the reports_progress() decorator for whole-function
contexts, or the progress_reporter() context manager for narrower
contexts.

It is the responsibility of the client to manage any thread-safety
issues. You should assume that progress reporting functions can be
called asynchronously, at any time, from the main thread.

Example::

  _progress_message = ""

  def _update_foo_progress(i, n):
      global _progress_message
      _progress_message = "{i} of {n} complete".format(i=i, n=n)

  def _report_foo_progress(stream):
      print(_progress_message, file=stream)

  @reports_progress(_report_foo_progress)
  def foo(n):
  for i in range(n):
      _update_foo_progress(i, n)

  # ...

  signal.signal(signal.SIGINFO,
                lambda *args: report_progress())

"""

from contextlib import contextmanager
from functools import wraps

# Currently installed zero-argument callables used to report progress.
import sys

_reporters = []  # pylint: disable=invalid-name


def report_progress(stream=None):
    """Report progress from any currently installed reporters.

    Args:
        stream: The text stream (default: sys.stderr) to which
            progress will be reported.
    """
    if stream is None:
        stream = sys.stderr
    for reporter in _reporters:
        reporter(stream)


@contextmanager
def progress_reporter(reporter):
    """A context manager to install and remove a progress reporting function.

    Args:
        reporter: A zero-argument callable to report progress.
            The callable provided should have the means to both
            retrieve and display current progress information.
    """
    install_progress_reporter(reporter)
    yield
    uninstall_progress_reporter(reporter)


def reports_progress(reporter):
    """A decorator factory to mark functions which report progress.

    Args:
        reporter: A zero-argument callable to report progress.
            The callable provided should have the means to both
            retrieve and display current progress information.
    """

    def decorator(func):  # pylint: disable=missing-docstring
        @wraps(func)
        def wrapper(*args, **kwargs):  # pylint: disable=missing-docstring
            with progress_reporter(reporter):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def install_progress_reporter(reporter):
    """Install a progress reporter.

    Where possible prefer to use the progress_reporter() context
    manager or reports_progress() decorator factory.

    Args:
        reporter: A zero-argument callable to report progress.
            The callable provided should have the means to both
            retrieve and display current progress information.
    """
    _reporters.append(reporter)


def uninstall_progress_reporter(reporter):
    """Uninstall a progress reporter.

    Where possible prefer to use the progress_reporter() context
    manager or reports_progress() decorator factory.

    Args:
        reporter: A callable previously installed by
            install_progress_reporter().
    """
    _reporters.remove(reporter)
