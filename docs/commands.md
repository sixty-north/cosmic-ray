# Commands

TODO: This is pretty wildly out of date!

## Details of Common Commands

Most Cosmic Ray commands use a verb-options pattern, similar to how git does
things.

Possible verbs are:

+ baseline
+ counts
+ [exec](#exec)
+ help
+ [init](#init)
+ load
+ operators
+ [dump](#dump)
+ run
+ survival-rate
+ test-runners
+ worker

Detailed information on each command can be found by running
`cosmic-ray help <command>` in the terminal.

Cosmic Ray also installs a few other separate commands for producing various
kinds of reports. These commands are:

+ cr-report: provides a report on the status of a session
+ cr-rate: prints the survival rate of a session

Use these by piping the output of `cosmic-ray dump` into them. For example:

```shell
$ cosmic-ray dump test_session | cr-report
$ cosmic-ray dump test_session | cr-rate
```

### Verbosity: Getting more Feedback when Running

The base command, `cosmic-ray`, has a single option: `--verbose`. The
`--verbose` option changes the internal logging level from `WARN` to `INFO`
and thus prints more information to the terminal.

When used with `init`, `--verbose` will list how long it took to create the
mutation list and will also list which modules were found:

```shell
(.venv-pyerf) ~/PyErf$ cosmic-ray --verbose init --baseline=2 test_session pyerf -- pyerf/tests
INFO:root:timeout = 0.259958 seconds
INFO:root:Modules discovered: ['pyerf.tests', 'pyerf.tests.test_pyerf', 'pyerf.pyerf', 'pyerf', 'pyerf.__about__']
(.venv-pyerf) C:\dev\PyErf>cosmic-ray --verbose init --baseline=2 test_session pyerf --exclude-modules=.*tests.* -- pyerf/tests
INFO:root:timeout = 0.239948 seconds
INFO:root:Modules discovered: ['pyerf.pyerf', 'pyerf', 'pyerf.__about__']
```

When used with `exec`, `--verbose` displays which mutation is currently being
tested:

```shell
(.venv-pyerf) ~/PyErf$ cosmic-ray --verbose exec test_session
INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '0', 'unittest', '--', 'pyerf/tests']
INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '1', 'unittest', '--', 'pyerf/tests']
INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '2', 'unittest', '--', 'pyerf/tests']
INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '3', 'unittest', '--', 'pyerf/tests']
INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '4', 'unittest', '--', 'pyerf/tests']
INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '5', 'unittest', '--', 'pyerf/tests']
INFO:cosmic_ray.tasks.worker:executing: ['cosmic-ray', 'worker', 'pyerf.pyerf', 'number_replacer', '6', 'unittest', '--', 'pyerf/tests']
```

The `--verbose` option does not add any additional information to the `dump`
verb.

### Command: init

The `init` verb creates a list of mutations to apply to the source code. It
has the following optional arguments:

+ `--no-local-import`: Allow importing module from the current directory.
+ `--test-runner=R`: Use a different test runner, such as pytest or nose.
+ `exclude-modules=P`: Exclude modules matching this regex pattern from
  mutation.

Some packages place the tests within a sub-package of the main one:

```
C:\dev\PyErf
¦   .gitignore
¦   .travis.yml
¦   CHANGELOG.md
¦   LICENSE
¦   README.rst
¦   requirements-dev.txt
¦   setup.py
¦
+---docs
¦       conf.py
¦       index.rst
¦       make.bat
¦       Makefile
¦
+---pyerf
    ¦   __init__.py
    ¦   __about__.py
    ¦   pyerf.py
    ¦
    +---tests
            __init__.py
            test_pyerf.py
```

As mentioned in [here](#An-important-note-on-separating-tests-and-production-code),
this can be handled via the `--exlcuded-modules` flag. With the example above,
the command to run would be from the Project directory (`C:\dev\PyErf`):

```
cosmic-ray init --baseline=2 test_session pyerf --exclude-modules=.*tests.* -- pyerf/tests
```

### Command: exec

The `exec` command is what actually runs the mutation testing. There is only
one optional argument: `--dist`. See
[Running distributed mutation testing](#running-distributed-mutation-testing)
for details.

### Command: dump

The `dump` command writes a detailed JSON representation of a session to stdout.

```shell
$ cosmic-ray dump test_session
{"data": ["<TestReport 'test_project/tests/test_adam.py::Tests::test_bool_if' when='call' outcome='failed'>"], "test_outcome": "killed", "worker_outcome": "normal", "diff": ["--- mutation diff ---", "--- a/Users/sixtynorth/projects/sixty-north/cosmic-ray/test_project/adam.py", "+++ b/Users/sixtynorth/projects/sixty-north/cosmic-ray/test_project/adam.py", "@@ -20,7 +20,7 @@", "     return (not object())", " ", " def bool_if():", "-    if object():", "+    if (not object()):", "         return True", "     raise Exception('bool_if() failed')", " "], "module": "adam", "operator": "cosmic_ray.operators.boolean_replacer.AddNot", "occurrence": 0, "line_number": 32, "command_line": ["cosmic-ray", "worker", "adam", "add_not", "0", "pytest", "--", "-x", "tests"], "job_id": "c2bb71e6203d44f6af42a7ee35cb5df9"}
. . .
```

Generally you'll want to pipe this output into another tool to generate some
sort of report. For example, you can find the survival rate of a session by
piping `cosmic-ray dump` into `cr-rate`:

```shell
$ cosmic-ray dump test_session | cr-rate
```

`dump` is designed to allow users to develop their own reports. To do this, you
need a program which reads a series of JSON structures from stdin. See the
`cr-rate` and `cr-report` tools included with Cosmic Ray for more details.

`cosmic-ray dump` **can** be run while `exec` is running! This is
super useful for seeing how far along a your mutation testing is:

```shell
# Run exec in the background
(.venv-pyerf) ~/PyErf$ cosmic-ray exec test_session &
(.venv-pyerf) ~/PyErf$ cosmic-ray dump test_session | cr-report
total jobs: 682
complete: 18 (2.64%)
survival rate: 0.00%
```
