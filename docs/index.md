# Cosmic Ray: mutation testing for Python

*"Four human beings -- changed by space-born cosmic rays into something more than merely human."*
*— The Fantastic Four*

Cosmic Ray is a tool for performing mutation testing on Python
code.

## N.B.! Cosmic Ray is still learning how to walk!

At this time Cosmic Ray is young and incomplete. It doesn't support
all of the mutations it should, its output format is crude, it only
supports some forms of test discovery, it may fall over on exotic
modules...[the list goes on and on](https://github.com/sixty-north/cosmic-ray/issues). Still,
for the adventurous it *does* work. Hopefully things will improve
fairly rapidly.

And, of course, patches and ideas are welcome.

## Quickstart

If you just want to get down to the business of finding and killing
mutants, here's what you do:

1. Install Cosmic Ray

    ```
    pip install cosmic_ray
    ```

2. Initialize a Cosmic Ray session

    ```
    cosmic-ray init --baseline=10 <session name> <module name> -- <test directory>
    ```

3. Execute the session:

    ```
    cosmic-ray exec <session name>
    ```

4. View the results:

    ```
    cosmic-ray report <session name>
    ```

This will print out a bunch of information about what Cosmic Ray did, including
what kinds of mutants were created, which were killed, and –
chillingly – which survived.

### A concrete example: running the `adam` unittests

Cosmic Ray includes a number of unit tests which perform mutations against a
simple module called `adam`. As a way of test driving Cosmic Ray, you can run
these tests, too, like this:

```
cd test_project
cosmic-ray init --baseline=10 example-session adam -- tests
cosmic-ray --verbose exec example-session
cosmic-ray report example-session
```

In this case we're passing the `--verbose` flag to the `exec` command so that
you can see what Cosmic Ray is doing. If everything goes as expected, the
`report` command will report a 0% survival rate.

## Installation

You can install Cosmic Ray using `pip`:

```
pip install cosmic_ray
```

Or you can use the supplied `setup.py`:

```
python setup.py install
```

Both of these approaches will install the Cosmic Ray package and
create an executable called `cosmic-ray`.

### Virtual environments

You'll often want to install Cosmic Ray into a virtual environment. However, you
generally *don't* want to install it into its own. Rather, you want to install
it into the virtual environment of the project you want to test. This ensures
that the test runners have access to the modules they are supposed to test.

### Sessions

Cosmic Ray has a notion of *sessions* which encompass an entire mutation testing
run. Essentially, a session is a database which records the work that needs to
be done for a run. Then as results are available from workers that do the actual
testing, the database is updated with results. By having a database like this,
Cosmic Ray can safely stop in the middle of a (potentially very long) session
and be restarted. Since the session knows which work is already completed, it
can continue where it left off.

Sessions also allow for arbitrary post-facto analysis and report generation.

### Initializing sessions

Before you can do mutation testing with Cosmic Ray, you need to first initialize
a session. You can do this using the `init` command. With this command you tell
Cosmic Ray a) the name of the session, b) which module(s) you wish to mutate and
c) the location of the test suite. For example, if you've a package named
`allele` and if the `unittest` tests for the package are all under the directory
`allele_tests`, you would run `cosmic-ray init` like this:

```
cosmic-ray init --baseline=2 test_session allele -- allele_tests
```

You'll notice that this creates a new file called "test_session.json". This the
database for your session.

There are a number of other options you can pass to the `init` command;
see the help message for more details.

### An important note on separating tests and production code

Cosmic Ray has a relatively simple view of how to mutate modules. Fundamentally,
it will attempt to mutate any and all code in a module. This means that if you
have test code in the same module as your code under test, Cosmic Ray will
happily mutate the test code along with the production code. This is probably
not what you want.

The best way to avoid this problem is to keep your test code in separate modules
from your production code. This way you can tell Cosmic Ray precisely what to
mutate.

Ideally, your test code will be in a different package from your production
code. This way you can tell Cosmic Ray to mutate an entire package without
needing to filter anything out. However, if your test code is in the same
package as your production code (a common configuration), you can use the
`--exclude-modules` flag of `cosmic-ray init` to prevent mutation of your tests.

Given the choice, though, we recommend keeping your tests outside of the package
for your code under test.

### Executing tests

Once a session has been initialized, you can start executing tests by using the
`exec` command. This command just needs the name of the session you provided to
`init`:

```
cosmic-ray exec test_session
```

Normally this won't produce any output unless there are errors.

### Viewing the results

Once your tests have completed, you can view the results using the `report` command:

```
cosmic-ray report test-session
```

This will give you detailed information about what work was done, followed by a
summary of the entire session.

### Short-cut: the `run` command

Originally Cosmic Ray didn't have a notion of sessions, and didn't distinguish
between initialization and execution of the tests. It did all of its work using
the `run` command.

Recent versions of Cosmic Ray still support the `run` command. All this command
does is first do an `init` followed by an `exec`. This can be convenient for
small test runs.

Be aware, however, that `init` **can destroy an existing session database**! If
you've got a session database with results representing hours of execution, you
probably don't want to delete it! So be aware that using the `init` or `run`
command have the potential to delete data.

### Test runners

Cosmic Ray supports multiple *test runners*. A test runner is simply a
plugin that supports a particular way of running tests. For example,
there is a test runner for tests written with the standard `unittest`
module, and there's another for tests written using
[`py.test`](pytest.org).

To specify a particular test runner when running Cosmic Ray, pass the
`--test-runner` flag to the `init` subcommand. For example, to use the
`pytest` runner you would use:

```
cosmic-ray init --test-runner=pytest test_session allele -- allele_tests
```

To get a list of the available test runners, use the `test-runners`
subcommand:
```
cosmic-ray test-runners
```

Test runners require information about which tests to run, flags controlling
their behavior, and so forth. Since each test runner implementation takes
different kinds of information, we allow users to pass arbitrary lists of
arguments to test runners. When running the `cosmic-ray init` command,
everything after the lone `--` token is passed verbatim to the test runner
initializer.

For example, the command:
```
cosmic-ray init --test-runner=pytest sess allele -- -x -k test_foo allele_tests
```

would pass the list `['-x', '-k', 'test_foo', 'allele_tests']` to the pytest
runner initializer. This plugin passes this list directly to the `pytest.main()`
function which treats them as command line arguments; in this case, it means
"exit on first failure, only running tests under 'allele_tests' which match
'test_foo'". Each test runner will accept different arguments, so see their
documentation for details on how to use them.

### Specifying test timeouts

One difficulty mutation testing tools have to face is how to deal with
mutations that result in infinite loops (or other pathological runtime
effects). Cosmic Ray takes the simple approach of using a *timeout* to
determine when to kill a test and consider it *incompetent*. That is,
if a test of a mutant takes longer than the timeout, the test is
killed, and the mutant is marked incompetent.

There are two ways to specify timeout values to Cosmic Ray. The first
is through the `--timeout` flag for the `init` subcommand. This flags
specifies an absolute number of seconds that a test will be allowed to
run. After the timeout is up, the test is killed. For example, to
specify that tests should timeout after 10 seconds, use:
```
cosmic-ray init --timeout=10 test_session allele -- allele/tests
```

The second way is by using a baseline timing. To use this technique,
pass the `--baseline` argument to the `init` subcommand. When Cosmic
Ray sees this flag it will make an initial run of the tests on an
un-mutated version of the module under test. The amount of time this
takes is considered the *baseline timing*. Then, Cosmic Ray multiplies
this baseline timing by the value of `--baseline` and this final value
is used as the timeout for tests. For example, to tell Cosmic Ray to
timeout tests when they take 3 times longer than a baseline run, use:
```
cosmic-ray init --baseline=3 test_session allele -- allele/tests
```

This baseline technique is particularly useful if your testsuite
runtime is in flux.

### Running with a config file

For many projects you'll probably be running the same `cosmic-ray`
command over and over. Instead of having to remember and retype
potentially complex commands each time, you can store `cosmic-ray`
commands in a config file. You can then execute these commands by
passing the `load` command to `cosmic-ray`.

Each line in the config file is treated as a separate command-line
argument to `cosmic-ray`. Empty lines in the file are skipped, and you
can have comments in config files that start with `#`.

So, for example, if you need to invoke this command for your project:

```
cosmic-ray run --verbose --timeout=30 --no-local-import --baseline=2 allele -- allele/tests/unittests
```

you could instead create a config file, `cr-allele.conf`, with these
contents:

```
init
--verbose     # this can be useful for debugging
--timeout=30  # this is plenty of time
--no-local-import
--baseline=2
test_session
allele
--
allele/tests/unittests
```

Then to run the command in that config file:

```
cosmic-ray load cr-allele.conf
```

and it will have the same effect as running the original command.

## Details of Common Commands

Cosmic-Ray uses a verb-options pattern for commands, similar to how git does
things.

Possible verbs are:

+ baseline
+ counts
+ [exec](#exec)
+ help
+ [init](#init)
+ load
+ operators
+ [report](#report)
+ run
+ survival-rate
+ test-runners
+ worker

Detailed information on each command can be found by running
`cosmic-ray help <command>` in the terminal.

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

The `--verbose` option does not add any additional information to the `report`
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

## Distributed testing with Celery

One of the main practical challenges to mutation testing is that it can take a
long time. Even on moderately sized projects, you might need millions of
individual mutations and test runs. This can be prohibitive to run on a single
system.

One way to cope with these long runtimes is to parallelize the mutation and
testing procedures. Fortunately, mutation testing is
[embarassingly parallel in nature](https://en.wikipedia.org/wiki/Embarrassingly_parallel),
so we can apply some relatively simple techniques to get really nice scaling up
of the work. We've chosen to use the
[Celery distributed task queue](http://www.celeryproject.org/) to spread work
across multiple nodes.

The basic idea is very simple. Celery lets you start multiple *workers* which
listen for commands from a task queue. A central process creates all of the
commands for a mutation testing run, and these commands are distributed to the
workers as they become available. When a worker receives a command, it starts a
*new* python process (using the `worker` subcommand to Cosmic Ray) which
performs a single mutation and runs the test suite.

Spawning a separate process for each test suite may seem expensive. However,
it's the best way we have for ensuring that pathological mutants can't somehow
corrupt the runtime of the worker processes. And ultimately the cost of starting
the process is likely to be very small compared to the runtime of the test
suite.

By its nature, Celery lets you start workers on as many systems as you want,
all connected to the same task queue. So you could potentially have thousands of
workers performing mutation testing runs, giving nearly perfect scaling! While
not everyone has thousands of machines on hand to do their testing work, it's
conceivable that Cosmic Ray will one day be able to work with machines on
commodity cloud providers, meaning that highly-scaled mutation testing for
Python will be available to anyone who wants it.

### Installing RabbitMQ

Celery is primarily a Python API atop the [RabbitMQ](https://www.rabbitmq.com/)
task queue. As such, if you want to use Cosmic Ray in distributed mode you first
need to install RabbitMQ and run the server. The steps for installing and running RabbitMQ are covered in detail at that project's site, so go there for more information. Make sure the RabbitMQ server is installated and running before going any further with distributed execution.

### Starting distributed worker processes

Once RabbitMQ is running, you need to start some worker processes which will do the actualy mutation testing. Start one or more worker processes like this:
```
celery -A cosmic_ray.tasks.worker worker
```

You should do this, of course, from the virtual environment into which you've
installed Cosmic Ray. Similary, you need to make sure that the worker is in an
environment in which it can import the modules under test. Generally speaking,
you can meet both of these criteria if you install Cosmic Ray into and run
workers from a virtual environment into which you've installed the modules under
test.

### Running distributed mutation testing

After you've started your workers, the only different between local and
distributed tesing is that you need to pass `--dist` to the `cosmic-ray exec`
command to do distributed testing. So a full distributed testing run would look something like this:
```
cosmic-ray init --baseline=3 session-name my_module -- tests
cosmic-ray exec --dist session-name
cosmic-ray report session-name
```

## Tests

Cosmic Ray has a number of test suites to help ensure that it works. The first
suite is a [pytest](http://pytest.org/) test suite that validates some if its
internals. You can run that like this:

```
py.test cosmic_ray/test
```

(Note that these unit tests don't require any workers to be running).

There is also a set of tests which verify the various mutation operators. These
tests comprise a specially prepared body of code, `adam.py`, and a full-coverage
test-suite. The idea here is that Cosmic Ray should be 100% lethal against the
mutants of `adam.py` or there's a problem.

These tests can be run via both the standard `unittest` and `py.test`. In both
cases, first make sure a worker (or several) is running. Then go to the
`test_project` directory:

```
cd test_project
```

Run the operator tests with `unittest` like this:

```
cosmic-ray load cosmic-ray.unittest.conf
```

View the results of this test with `report`:

```
cosmic-ray report adam_tests.unittest
```

You should see a 0% survival rate at the end of the report.

Likewise you can run with `py.test` like this:

```
cosmic-ray load cosmic-ray.pytest.conf
```

The report will be available from the `adam_tests.pytest` session:

```
cosmic-ray report adam_tests.pytest
```

## Theory

Mutation testing is conceptually simple and elegant. You make certain
kinds of controlled changes (mutations) to your code, and then you
run your test suite over this mutated code. If your test suite fails,
then we say that your tests "killed" (i.e. detected) the mutant. If
the changes cause your code to simply crash, then we say the mutant is
"incompetent". If your test suite passes, however, we say that the
mutant has "survived".

Needless to say, we want to
[kill all of the mutants](http://www.troll.me/images/x-all-the-things/kill-all-the-mutants.jpg).

The goal of mutation testing is to verify that your test suite is
actually testing all of the parts of your code that it needs to, and
that it is doing so in a meaningful way. If a mutant survives your
test suite, this is an indication that your test suite is not
adequately checking the code that was changed. This means that either
a) you need more or better tests or b) you've got code which you don't
need.

You can read more about mutation testing at
[the repository of all human knowledge](http://en.wikipedia.org/wiki/Mutation_testing). Lionel
Brian has a
[nice set of slides](http://www.uio.no/studier/emner/matnat/ifi/INF4290/v10/undervisningsmateriale/INF4290-Mutest.pdf)
introducing mutation testing as well.

## Implementation

Cosmic Ray works by parsing the module under test (MUT) and its
submodules into abstract syntax trees using
[the `ast` module](https://docs.python.org/3/library/ast.html). It
then uses
[the `ast.NodeTransformer` class](https://docs.python.org/3/library/ast.html#ast.NodeTransformer)
to make systematic mutations to the ASTs.

For each individual mutation, Cosmic Ray modifies the Python runtime
environment to replace the MUT with the mutated version. It then uses
[`unittest`'s "discovery" functionality](https://docs.python.org/3/library/unittest.html#test-discovery)
to discover your tests and run them against the mutant code.

In effect, the mutation testing algorithm is something like this:

```python
for mod in modules_under_test:
    for op in mutation_operators:
        for site in mutation_sites(op, mod):
            mutant_ast = mutate_ast(op, mod, site)
            replace_module(mod.name, compile(mutant_ast)

            try:
                if discover_and_run_tests():
                    print('Oh no! The mutant survived!')
                else:
                    print('The mutant was killed.')
            except Exception:
                print('The mutant was incompetent.')
```

Obviously this can result in a lot of tests, and it can take some time
if your test suite is large and/or slow.
