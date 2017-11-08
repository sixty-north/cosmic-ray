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
primary examples of execution engines are the *local* and *celery3* engines. The
local engine executes tests serially on the local machine; the celery3 engine
distributes tests to remote workers using the Celery (v3) system. Other kinds of
engines might run tests on a cloud service or using other task distribution
technology.

Execution engines have broad control over how they execute tests. During the
execution phase they are given a sequence of pending mutations to execute, and
it's their job to execute the tests in the appropriate context and return a
result. Cosmic Ray doesn't impose any real constraints on how engines accomplish
this.

Engines can require arbitrarily complex infrastructure and configuration. For
example, the celery3 engine requires you to run rabbitmq and to attach one or
more worker tasks to that queue.

Execution engines are implemented as plugins to Cosmic Ray. They are dynamically
discovered, and users can create their own execution engines if they want.
Cosmic Ray includes two execution engines plugins, local and celery3.

Configurations
==============

A *configuration* is a YAML file that describes the work that Cosmic Ray will
do. For example, it tells Cosmic Ray which modules to mutate, what test runner
to use, which tests to run, and so forth. You need to create a config before
doing any real work with Cosmic Ray.

You can create a skeleton config by running `cosmic-ray new-config <config
file>`. This will ask you a series of questions and create a config from the
answers. Note that this config will generally be incomplete and require you to
edit it for completeness.

Another way to create a skeleton config is to run `cosmic-ray exec`. If you
specify a non-existent config file for this command, Cosmic Ray will ask you the
same questions as in `cosmic-ray new-config` to create one.

In many Cosmic Ray example we'll use the name "config.yml" for configurations.
You are not required to use this name, however. You can use any file name you
want for your configurations.

**IMPORTANT**: The full set of configuration options are not currently well
documented. Each plugin can, in principle and often in practice, use their own
specialized configuration options. We need to work on making the documentation
of these options automatic and part of the plugin API. For detail on
configuration options, the best place to check is currently in the
`test_project` directory.

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

Before you can do mutation testing with Cosmic Ray, you need to first initialize
a session. You can do this using the ``init`` command. With this command you
tell Cosmic Ray a) the name of the session, b) which module(s) you wish to
mutate and c) the location of the test suite. For example, to mutate the package
`allele`, use the `unittest` test-runner to run the tests in `allele_tests`, and
use the `local` execution engine, you could first need to create a configuration
like this:

.. code-block:: yaml

   # allele_config.yml
   module: allele

   baseline: 10

   exclude-modules:

   test-runner:
     name: unittest
     args: allele_tests

   execution-engine:
     name: local

You would run ``cosmic-ray init`` like this:

::

    cosmic-ray init allele_config.yml allele_session

You'll notice that this creates a new file called "allele\_session.json".
This the database for your session.

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

    cosmic-ray dump test_session | cr-report

This will give you detailed information about what work was done,
followed by a summary of the entire session.

Test runners
============

Cosmic Ray supports multiple *test runners*. A test runner is simply a
plugin that supports a particular way of running tests. For example,
there is a test runner for tests written with the standard ``unittest``
module, and there's another for tests written using
```pytest`` <pytest.org>`__.

To specify a particular test runner when running Cosmic Ray, specify it in your
config at the "test-runner:name" key:

.. code-block:: yaml

  # config.yml
  test-runner:
    name: <test runner name>

To get a list of the available test runners, use the ``test-runners``
subcommand:

::

    cosmic-ray test-runners

Test runners require information about which tests to run, flags controlling
their behavior, and so forth. Since each test runner implementation takes
different kinds of information, we pass the value of "test-runner:args" to the
test runner. For example, with this config:

.. code-block:: yaml

   # config.yml
   test-runner:
     name: pytest
     args: -x -k test_foo allele_tests

would pass the string ``-x -k test_foo allele_tests`` to the
pytest runner initializer. This plugin passes this string directly to the
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
through the ``timeout`` configuration key. This key
specifies an absolute number of seconds that a test will be allowed to
run. After the timeout is up, the test is killed. For example, to
specify that tests should timeout after 10 seconds, use:

.. code-block:: yaml

   # config.yml
   timeout: 10

The second way is by using a baseline timing. To use this technique,
set the ``baseline`` config key. When Cosmic
Ray sees this key it will make an initial run of the tests on an
un-mutated version of the module under test. The amount of time this
takes is considered the *baseline timing*. Then, Cosmic Ray multiplies
this baseline timing by the value of ``baseline`` and this final value
is used as the timeout for tests. For example, to tell Cosmic Ray to
timeout tests when they take 3 times longer than a baseline run, use

.. code-block:: yaml

   # config.yml
   baseline: 3

This baseline technique is particularly useful if your testsuite runtime
is in flux.
