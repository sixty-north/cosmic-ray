Commands
========

TODO: This is pretty wildly out of date! Perhaps we can use value-add to do this.

Details of Common Commands
--------------------------

Most Cosmic Ray commands use a verb-options pattern, similar to how git
does things.

Possible verbs are:

- `exec <#exec>`__
- help
- `init <#init>`__
- load
- new-config
- operators
- `dump <#dump>`__
- run
- worker
- apply

Detailed information on each command can be found by running
``cosmic-ray help <command>`` in the terminal.

Cosmic Ray also installs a few other separate commands for producing
various kinds of reports. These commands are:

-  cr-report: provides a report on the status of a session
-  cr-rate: prints the survival rate of a session
-  cr-html: prints an HTML report on a session

Verbosity: Getting more Feedback when Running
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The base command, ``cosmic-ray``, has a single option: ``--verbose``.
The ``--verbose`` option changes the internal logging level from
``WARN`` to ``INFO`` and thus prints more information to the terminal.

When used with ``init``, ``--verbose`` will list how long it took to
create the mutation list and will also list which modules were found:

.. code:: shell

    (.venv-pyerf) ~/PyErf$ cosmic-ray --verbose init --baseline=2 test_session pyerf -- pyerf/tests
    INFO:root:timeout = 0.259958 seconds
    INFO:root:Modules discovered: ['pyerf.tests', 'pyerf.tests.test_pyerf', 'pyerf.pyerf', 'pyerf', 'pyerf.__about__']
    (.venv-pyerf) C:\dev\PyErf>cosmic-ray --verbose init --baseline=2 test_session pyerf --exclude-modules=.*tests.* -- pyerf/tests
    INFO:root:timeout = 0.239948 seconds
    INFO:root:Modules discovered: ['pyerf.pyerf', 'pyerf', 'pyerf.__about__']

When used with ``exec``, ``--verbose`` displays which mutation is
currently being tested:

.. code:: shell

    (.venv-pyerf) ~/PyErf$ cosmic-ray --verbose exec test_session
    INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '0', 'unittest', '--', 'pyerf/tests']
    INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '1', 'unittest', '--', 'pyerf/tests']
    INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '2', 'unittest', '--', 'pyerf/tests']
    INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '3', 'unittest', '--', 'pyerf/tests']
    INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '4', 'unittest', '--', 'pyerf/tests']
    INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '5', 'unittest', '--', 'pyerf/tests']
    INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '6', 'unittest', '--', 'pyerf/tests']

The ``--verbose`` option does not add any additional information to the
``dump`` verb.

Command: init
~~~~~~~~~~~~~

The ``init`` verb creates a list of mutations to apply to the source
code. It has the following optional arguments:

-  ``--no-local-import``: Allow importing module from the current
   directory.

The ``init`` verb use following entries from the configuration file:

- ``[cosmic-ray] exclude-modules = []``: Exclude modules matching those glob
  patterns from mutation. Use ``glob.glob`` syntax.

  Sample for django projects:

  ::

   exclude-modules = ["*/tests/*", "*/migrations/*"]


As mentioned in
`here <#An-important-note-on-separating-tests-and-production-code>`__,
test directory can be handled via the ``excluded-modules`` option.

The list of files that will be mutate effectively can be show by running
``cosmic-ray init`` with INFO debug level:

::

 cosmic-ray init -v INFO

Command: exec
~~~~~~~~~~~~~

The ``exec`` command is what actually runs the mutation testing. There
is only one optional argument: ``--dist``. See `Running distributed
mutation testing <#running-distributed-mutation-testing>`__ for details.

Command: dump
~~~~~~~~~~~~~

The ``dump`` command writes a detailed JSON representation of a session
to stdout.

.. code:: shell

    $ cosmic-ray dump test_session
    {"data": ["<TestReport 'test_project/tests/test_adam.py::Tests::test_bool_if' when='call' outcome='failed'>"], "test_outcome": "killed", "worker_outcome": "normal", "diff": ["--- mutation diff ---", "--- a/Users/sixtynorth/projects/sixty-north/cosmic-ray/test_project/adam.py", "+++ b/Users/sixtynorth/projects/sixty-north/cosmic-ray/test_project/adam.py", "@@ -20,7 +20,7 @@", "     return (not object())", " ", " def bool_if():", "-    if object():", "+    if (not object()):", "         return True", "     raise Exception('bool_if() failed')", " "], "module": "adam", "operator": "cosmic_ray.operators.boolean_replacer.AddNot", "occurrence": 0, "line_number": 32, "command_line": ["cosmic-ray", "worker", "adam", "add_not", "0", "pytest", "--", "-x", "tests"], "job_id": "c2bb71e6203d44f6af42a7ee35cb5df9"}
    . . .


``dump`` is designed to allow users to develop their own reports. To do
this, you need a program which reads a series of JSON structures from
stdin.

Concurrency
===========

Note that most Cosmic Ray commands can be safely executed while ``exec`` is
running. One exception is ``init`` since that will rewrite the work manifest.

For example, you can run ``cr-report`` on a session while that session is being
executed. This will tell you what progress has been made.
