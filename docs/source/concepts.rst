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
:mod:`cosmic_ray.operators.break_continue`. As its name
implies, this operator mutates code by replacing ``break`` with ``continue``.
During
the initialization of a session, this operator identifies all of the locations
in the code where this mutation can be applied. Then, during execution of a
session, it actually mutates the code by replacing ``break`` nodes with
``continue``
nodes.

Operators are exposed to Cosmic Ray via plugins, and users can choose to extend
the available operator set by providing their own operators. Operators are
implemented as subclasses of :class:`cosmic_ray.operators.operator.Operator`.

Distributors
============

*Distributors* determine the context in which tests are executed. The primary examples of distributors are
:class:`cosmic_ray.distribution.local.LocalDistributor` and :class:`cosmic_ray.distribution.http.HttpDistributor`. The
local distributor tests on the local machine, modifying an existing copy of the code in-place, running each test
serially with no concurrency.

The http distributor distributes tests to remote workers via HTTP. There can be any number of workers, and they can run the
tests in parallel. Because of this concurrency, each HTTP worker will generally have its own copy of the code under
test.

Distributors have broad control over how they execute tests. During the execution phase they are given a sequence of
pending mutations to execute, and it's their job to execute the tests in the appropriate context and return a result.
Cosmic Ray doesn't impose any real constraints on how distributors accomplish this.

Distributors can require arbitrarily complex infrastructure and configuration. For example, the HTTP distributor requires
you to start the workers prior to starting execution, and it requires that you provide each worker with its own 
copy of the code under test.

Distributors are implemented as plugins to Cosmic Ray. They are dynamically discovered, and users can create their own
distributors. Cosmic Ray includes two execution engines plugins, *local* and *http*.

Configurations
==============

A *configuration* is a TOML file that describes the work that Cosmic Ray will do. For example, it tells Cosmic Ray which
modules to mutate, how to run tests, which tests to run, and so forth. You need to create a config before doing any real
work with Cosmic Ray.

You can create a skeleton config by running ``cosmic-ray new-config <config file>``. This will ask you a series of
questions and create a config from the answers. Note that this config will generally be incomplete and require you to
edit it for completeness.

In many Cosmic Ray examples we'll use the name "config.toml" for configurations. You are not required to use this name,
however. You can use any file name you want for your configurations.

.. important::

    The full set of configuration options are not currently well documented. Each plugin can, in principle and often in
    practice, use their own specialized configuration options. We need to work on making the documentation of these
    options automatic and part of the plugin API. For detail on configuration options, the best place to check is
    currently in the ``tests/example_project`` directory.

Sessions
========

Cosmic Ray has a notion of *sessions* which encompass an entire mutation testing run. Essentially, a session is a
database which records the work that needs to be done for a run. Then as results are available from workers that do the
actual testing, the database is updated with results. By having a database like this, Cosmic Ray can safely stop in the
middle of a (potentially very long) session and be restarted. Since the session knows which work is already completed,
it can continue where it left off.

Sessions also allow for arbitrary post-facto analysis and report generation.

Initializing sessions
---------------------

Before you can do mutation testing with Cosmic Ray, you need to first initialize a session. You can do this using the
``init`` command. With this command you tell Cosmic Ray a) the name of the session, b) which module(s) you wish to
mutate and c) the location of the test suite. For example, to mutate the package ``allele``, using the ``unittest`` to
run the tests in ``allele_tests``, and using the ``local`` execution engine, you could first need to create a
configuration like this:

.. code-block:: ini

    [cosmic-ray]
    module-path = "allele"
    timeout = 10
    excluded-modules = []
    test-command = python -m unittest allele_tests
    distributor.name = "local"

You would run ``cosmic-ray init`` like this:

::

    cosmic-ray init config.toml session.sqlite

You'll notice that this creates a new file called ``allele_session.sqlite``. This is the database for your session.

.. _test_suite:

Test suite
==========

To be able to kill the mutants Cosmic Ray uses your test cases. But the mutants are not considered "more dead" when more
test cases fail. Given that a single failing test case is sufficient to kill a mutant, it's a good idea to configure the
test runner to exit as soon as a failing test case is found.

For ``pytest`` and ``nose`` that can be achieved with the ``-x`` option.

.. _note_separation_test_code:

.. admonition:: An important note on separating tests and production code

    Cosmic Ray has a relatively simple view of how to mutate modules. Fundamentally, it will attempt to mutate any and all
    code in a module. This means that if you have test code in the same module as your code under test, Cosmic Ray will
    happily mutate the test code along with the production code. This is probably not what you want.

    The best way to avoid this problem is to keep your test code in separate modules from your production code. This way you
    can tell Cosmic Ray precisely what to mutate.

    Ideally, your test code will be in a different package from your production code. This way you can tell Cosmic Ray to
    mutate an entire package without needing to filter anything out. However, if your test code is in the same package as
    your production code (a common configuration), you can use the ``excluded-modules`` setting in your configuration to
    prevent mutation of your tests.

    Given the choice, though, we recommend keeping your tests outside of the package for your code under test.

Executing tests
---------------

Once a session has been initialized, you can start executing tests by using the ``exec`` command. This command
needs the config and the session you provided to ``init``:

.. code-block:: bash

    cosmic-ray exec config.toml session.sqlite

Normally this won't produce any output unless there are errors.

Viewing the results
-------------------

Once your tests have completed, you can view the results using the ``cr-report`` command:

.. code-block:: bash

    cr-report test_session.sqlite

This will give you detailed information about what work was done, followed by a summary of the entire session.

Test commands
=============

The ``test-command`` field of a configuration tells Cosmic Ray how to run tests. Cosmic Ray runs this command from
whatever directory you run the ``exec`` command (or, in the case of remote execution, in whatever directory the remote
command handler is running).

Timeouts
========

One difficulty mutation testing tools have to face is how to deal with mutations that result in infinite loops (or other
pathological runtime effects). Cosmic Ray takes the simple approach of using a *timeout* to determine when to kill a
test and consider it *incompetent*. That is, if a test of a mutant takes longer than the timeout, the test is killed,
and the mutant is marked incompetent.

You specify a test time through the ``timeout`` configuration key. This key specifies an absolute number of seconds that
a test will be allowed to run. After the timeout is up, the test is killed. For example, to specify that tests should
timeout after 10 seconds, use:

.. code-block:: ini

   # config.toml
   [cosmic-ray]
   timeout = 10
