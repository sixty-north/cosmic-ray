==========
 Concepts
==========

Cosmic Ray comprises a number of important and potentially confusing concepts.
In this section we'll look at each of these concepts, explaining their role in
Cosmic Ray and how they relate to other concepts. We'll also use this section to
establish the terminology that we'll use throughout the rest of the
documentation.

Operators
=========

An *operator* in Cosmic Ray is a class that represents a specific type of
mutation. The first role of an operator is to identify points in the code where
a specific mutation can be applied. The second role of an operator is to
actually perform the mutation when requested.

An example of an operator is
`cosmic_ray.operators.break_continue.ReplaceBreakWithContinue`. As its name
implies, this operator mutates code by replacing `break` with `continue`. During
the initialization of a session, this operator identifies all of the locations
in the code where this mutation can be applied. Then, during execution of a
session, it actually mutates the AST by replacing `break` nodes with `continue`
nodes.

Operators are exposed to Cosmic Ray via plugins, and if they want users can
extend the available operator set by providing their own operators. Operators
are implemented as subclasses of `cosmic_ray.operators.operator.Operator`.

Execution engines
=================

*Execution engines* determine the context in which tests are executed. The
primary examples of execution engines are the *local* and *celery* engines. The
local engine executes tests serially on the local machine; the celery engine
distributes tests to remote workers using the Celery system. Other kinds of
engines might run tests on a cloud service or using other task distribution
technology.

Execution engines have broad control over how they execute tests. During the
execution phase they are given a sequence of pending mutations to execute, and
it's their job to execute the tests in the appropriate context and return a
result. Cosmic Ray doesn't impose any real constraints on how engines accomplish
this.

Engines can require arbitrarily complex infrastructure and configuration. For
example, the celery engine requires you to run rabbitmq and to attach one or
more worker tasks to that queue.

Right now there are only two execution engines - local and celery - and they are
baked into Cosmic Ray. There are plans to turn execution engines into plugins,
however, and that will make it easier to add new execution engines.

Configurations
==============

Sessions
========

Cosmic Ray has a notion of *sessions* which encompass an entire mutation
testing run. Essentially, a session is a database which records the work
that needs to be done for a run. Then as results are available from
workers that do the actual testing, the database is updated with
results. By having a database like this, Cosmic Ray can safely stop in
the middle of a (potentially very long) session and be restarted. Since
the session knows which work is already completed, it can continue where
it left off.

Sessions also allow for arbitrary post-facto analysis and report
generation.

Initializing sessions
---------------------

Before you can do mutation testing with Cosmic Ray, you need to first
initialize a session. You can do this using the ``init`` command. With
this command you tell Cosmic Ray a) the name of the session, b) which
module(s) you wish to mutate and c) the location of the test suite. For
example, if you've a package named ``allele`` and if the ``unittest``
tests for the package are all under the directory ``allele_tests``, you
would run ``cosmic-ray init`` like this:

::

    cosmic-ray init --baseline=2 test_session allele -- allele_tests

You'll notice that this creates a new file called "test\_session.json".
This the database for your session.

There are a number of other options you can pass to the ``init``
command; see the help message for more details.

An important note on separating tests and production code
---------------------------------------------------------

Cosmic Ray has a relatively simple view of how to mutate modules.
Fundamentally, it will attempt to mutate any and all code in a module.
This means that if you have test code in the same module as your code
under test, Cosmic Ray will happily mutate the test code along with the
production code. This is probably not what you want.

The best way to avoid this problem is to keep your test code in separate
modules from your production code. This way you can tell Cosmic Ray
precisely what to mutate.

Ideally, your test code will be in a different package from your
production code. This way you can tell Cosmic Ray to mutate an entire
package without needing to filter anything out. However, if your test
code is in the same package as your production code (a common
configuration), you can use the ``--exclude-modules`` flag of
``cosmic-ray init`` to prevent mutation of your tests.

Given the choice, though, we recommend keeping your tests outside of the
package for your code under test.

Executing tests
---------------

Once a session has been initialized, you can start executing tests by
using the ``exec`` command. This command just needs the name of the
session you provided to ``init``:

::

    cosmic-ray exec test_session

Normally this won't produce any output unless there are errors.

Viewing the results
-------------------

Once your tests have completed, you can view the results using the
``cr-report`` command:

::

    cosmic-ray dump test-session | cr-report

This will give you detailed information about what work was done,
followed by a summary of the entire session.

Test runners
============

Cosmic Ray supports multiple *test runners*. A test runner is simply a
plugin that supports a particular way of running tests. For example,
there is a test runner for tests written with the standard ``unittest``
module, and there's another for tests written using
```pytest`` <pytest.org>`__.

To specify a particular test runner when running Cosmic Ray, pass the
``--test-runner`` flag to the ``init`` subcommand. For example, to use
the ``pytest`` runner you would use:

::

    cosmic-ray init --test-runner=pytest test_session allele -- allele_tests

To get a list of the available test runners, use the ``test-runners``
subcommand:

::

    cosmic-ray test-runners

Test runners require information about which tests to run, flags
controlling their behavior, and so forth. Since each test runner
implementation takes different kinds of information, we allow users to
pass arbitrary lists of arguments to test runners. When running the
``cosmic-ray init`` command, everything after the lone ``--`` token is
passed verbatim to the test runner initializer.

For example, the command:

::

    cosmic-ray init --test-runner=pytest sess allele -- -x -k test_foo allele_tests

would pass the list ``['-x', '-k', 'test_foo', 'allele_tests']`` to the
pytest runner initializer. This plugin passes this list directly to the
``pytest.main()`` function which treats them as command line arguments;
in this case, it means "exit on first failure, only running tests under
'allele\_tests' which match 'test\_foo'". Each test runner will accept
different arguments, so see their documentation for details on how to
use them.

Baselines and timeouts
======================

One difficulty mutation testing tools have to face is how to deal with
mutations that result in infinite loops (or other pathological runtime
effects). Cosmic Ray takes the simple approach of using a *timeout* to
determine when to kill a test and consider it *incompetent*. That is, if
a test of a mutant takes longer than the timeout, the test is killed,
and the mutant is marked incompetent.

There are two ways to specify timeout values to Cosmic Ray. The first is
through the ``--timeout`` flag for the ``init`` subcommand. This flags
specifies an absolute number of seconds that a test will be allowed to
run. After the timeout is up, the test is killed. For example, to
specify that tests should timeout after 10 seconds, use:

::

    cosmic-ray init --timeout=10 test_session allele -- allele/tests

The second way is by using a baseline timing. To use this technique,
pass the ``--baseline`` argument to the ``init`` subcommand. When Cosmic
Ray sees this flag it will make an initial run of the tests on an
un-mutated version of the module under test. The amount of time this
takes is considered the *baseline timing*. Then, Cosmic Ray multiplies
this baseline timing by the value of ``--baseline`` and this final value
is used as the timeout for tests. For example, to tell Cosmic Ray to
timeout tests when they take 3 times longer than a baseline run, use:

::

    cosmic-ray init --baseline=3 test_session allele -- allele/tests

This baseline technique is particularly useful if your testsuite runtime
is in flux.
