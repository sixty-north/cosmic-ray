.. _basic tutorial:

====================
Tutorial: The basics
====================

This tutorial will walk you through the steps needed to install, configure, and run Cosmic
Ray. 

Installation
============

First you'll need to install Cosmic Ray. The simplest (and generally best) way to do this is with ``pip``:

.. code-block:: bash

    pip install cosmic-ray

You'll generally want to do this in a virtual environment, but it's not required.

Installation from source
------------------------

If you need to install Cosmic Ray from source, first change to the directorying containing ``setup.py``. Then run::

    pip install .

Or, if you want to `install from source in "editable" mode <https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-e>`_, you can use the ``-e` flag::

    pip install -e .

Source module and tests
=======================

Mutation testing works by making small mutations to the *code under test* (CUT) and then running a test suite
over the mutated code. For this tutorial, then, we'll need to create our CUT and a test suite for it.

You should create a new directory which will contain the CUT, the tests, and eventually the Cosmic Ray data.
For the rest of this tutorial we'll refer to this new directory as ``ROOT`` (or ``$ROOT`` if we're showing shell code). 

Now create the file ``ROOT/mod.py`` with these contents:

.. literalinclude:: mod.1.py

This file contains your code under test, i.e. the code that Cosmic Ray will mutate. It's clearly very simple, and it has
very few opportunities for mutation, but it's sufficient for this tutorial. In fact, having simple code like this will
make it easier to see what Cosmic Ray is doing without getting bogged down by scale.

Next create the file ``ROOT/test_mod.py`` with these contents:

.. literalinclude:: test_mod.1.py

This contains the test suite for ``mod.py``. Cosmic Ray will not mutate this code. Rather, it will run this test suite
for every mutation that it creates.

Before moving on, let's make sure that the test suite works correctly:

.. code-block:: bash

    python -m unittest test_mod.py

This should show that all tests pass:

.. code-block:: bash

    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.000s

    OK    

If you see one test passing like this, then you're ready to continue!

Creating a configuration
========================

Before you do run any mutation tests, you need to create a *configuration*.
A configuration is a `TOML <https://toml.io/>`_ file that specifies the modules you want to mutate, the
test scripts to use, and so forth. A configuration is used to create a *session*,
something we'll look at in the next section.

The ``new-config`` command
--------------------------

You can create a configuration by hand if you want. In fact, you'll generally
need to edit them by hand to get the exact configuration you need. But you can
create an initial configuration using the ``new-config`` command. This will ask
you a series of questions and construct a new configuration based on your
answers.

To create your config for this tutorial, do this:

.. code-block:: bash

    cd $ROOT
    cosmic-ray new-config tutorial.toml

This will ask you a series of questions. Answer them like this:

.. code-block:: text

    [?] Top-level module path: mod.py
    [?] Test execution timeout (seconds): 10
    [?] Test command: python -m unittest test_mod.py
    -- MENU: Distributor --
      (0) http
      (1) local
    [?] Enter menu selection: 1   

This will create the file ``tutorial.toml`` with these contents:

.. literalinclude:: tutorial.toml.1
    :linenos:
    :language: toml

Configuration contents
~~~~~~~~~~~~~~~~~~~~~~

Let's examine the contents of this file before moving on. On line 1 we define the 'cosmic-ray' key in the TOML
structure; this key will contain all Cosmic Ray configuration information.

On line 2 we set the 'module-path' key to the string "mod.py":

.. literalinclude:: tutorial.toml.1
    :lines: 2
    :language: toml

This tells Cosmic Ray that we're going to be mutating the module in the file ``mod.py``. Every Cosmic Ray configuration
refers to a single top-level module that will be mutated, and in this case we're telling Cosmic Ray to mutate the
``mod`` module, contained in the file ``mod.py``.

.. note::

    The 'module-path' is a *path* to a file or directory, not the name of the module of package. If it's a file then
    Cosmic Ray will treat it as a single module, but if it's a directory then Cosmic Ray will treat it as a package.

    When working on a package, Cosmic Ray will apply mutations to all submodules in the package.

    Additionally, the 'module-path' can be a list of directories or files: `module-path = ["file1.py", "some_directory"]`

Line 3 tells Cosmic Ray the maximium amount of time to let a test run before it's considered a failure:

.. literalinclude:: tutorial.toml.1
    :lines: 3
    :language: toml

In this case, we're telling Cosmic Ray to kill a test if it runs longer than 10 seconds. This timeout is important because
some mutations can cause the tests to go into an infinite loop. Without timeout we'd never exit the test! It's important to 
set this timeout such that it's long enough for all legitimate tests.

Next, line 4 tells Cosmic Ray which modules to exclude from mutation:

.. literalinclude:: tutorial.toml.1
    :lines: 4
    :language: toml

In this case we're not excluding any, but there may be times when you need to skip certain modules, e.g. because 
you know that you don't have sufficient tests for them at the moment. This parameter expects glob-patterns, so to exclude
files that end with ``_test.py`` recursively for example, you would add ``"**/*_test.py"``.

Line 5 is one of the most critical lines in the configuration. This tells Cosmic Ray how to run your test suite:

.. literalinclude:: tutorial.toml.1
    :lines: 5
    :language: toml

In this case, our test suite uses the standard `unittest testing framework
<https://docs.python.org/3/library/unittest.html>`_, and the tests are in the file ``test_mod.py``.

The last two lines tell Cosmic Ray which "distributor" to use:

.. literalinclude:: tutorial.toml.1
    :lines: 7-8
    :language: toml

A distributor controls how mutation jobs are assigned to one or more workers so that they can (potentially) run in
parallel. In this case we're using the default 'local' distributor which only runs one mutation at a time. There are
other, more sophisticated distributors which we discuss elsewhere.

Create a session and baseline
=============================

Cosmic Ray uses a notion of *sessions* to encompass a full mutation testing
suite. Since mutation testing runs can take a long time, and since you might
need to stop and start them, sessions store data about the progress of a run.

.. note::

    Most Cosmic Ray commands allow you to increase their "verbosity" via the command line. This will make them print out
    more information about what they're doing. 

    Try adding "--verbosity INFO" to the command you run if you more details about
    what's going on!

Initializing a session
----------------------

The first step in a full testing run, then, is to initialize a session:

.. code-block:: bash

    cosmic-ray init tutorial.toml tutorial.sqlite

.. note::

    This command prepares all the mutations that will later be applied to code.
    As such, its execution time is proportional to the amount of code and
    the code complexitly. You can expect about 15-30s per 1kloc.

This will create a database file called ``tutorial.sqlite``. There is a record in the database for each mutation that
Cosmic Ray will perform, and Cosmic Ray will associate testing results with these records as it executes.

When does `init` need to be run?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`init` completely rewrites the session file you tell it to use, so you should not re-run `init` on a session that
contains any results that you want to keep. At the same time, if you change your configuration in a way that alters
which tests are run and which mutations are made, then you should re-initialize your session.

Generally speaking, if you change the 'module-path', 'timeout', 'excluded-modules', or 'test-command' parts of your
configuration, or if you change any of the filters you use, then you need to re-initialize your session and start over.
Any of these changes can affect the operations that the subsequent `exec` command will run.

Similarly, you need to create a new session with `init` whenever your code-under-test or your tests themselves change.
This is necessary because changes to the CUT will affect which mutations are made and changes to the tests affect which
tests are run.

Baselining
----------

Before running the full mutation suite, it's important to make sure that the test suite passes in the absence of any
mutations. If the test suite does *not* pass in the absence of mutations, then the results of the mutation testing are
essentially useless.

You can use the ``baseline`` command to check that the test suite passes on unmutated code:

.. code-block:: bash

    cosmic-ray --verbosity=INFO baseline tutorial.toml

This should report that the tests pass, something like this:

.. code-block:: text

    [07/23/21 10:00:20] INFO     INFO:root:Reading config from 'tutorial.toml'                                                                                                                                            config.py:103
                        INFO     INFO:cosmic_ray.commands.execute:Beginning execution                                                                                                                                     execute.py:45
                        INFO     INFO:cosmic_ray.testing:Running test (timeout=10.0): python -m unittest test_mod.py                                                                                                      testing.py:36
                        INFO     INFO:cosmic_ray.commands.execute:Job baseline complete                                                                                                                                   execute.py:43
                        INFO     INFO:cosmic_ray.commands.execute:Execution finished                                                                                                                                      execute.py:53
                        INFO     INFO:root:Baseline passed. Execution with no mutation works fine.       

If this command succeeds, then you're ready to start mutating code and testing it!

Examining the session with cr-report
====================================

Our session file, ``tutorial.sqlite``, is essentially a list of mutations that Cosmic Ray will perform on the
code under test. We haven't actually tested any mutants, so none of our mutations have testing results yet. With
that in mind, let's examine the contents of our session with the ``cr-report`` program:

.. code-block:: bash

    cr-report tutorial.sqlite --show-pending

This will produce output like this (though note that the test IDs will be different):

.. code-block:: text

    [job-id] f168ef23dff24b75846a730858fe0111
    mod.py core/NumberReplacer 0
    [job-id] 929a563b613242b48dae0f2de74ad2af
    mod.py core/NumberReplacer 1
    total jobs: 2
    no jobs completed

This is telling us that Cosmic Ray detected two mutations that it can make to our code, both using the
mutation operator "core/NumberReplacer". Without going into details, this means that Cosmic Ray has found
one or more numeric literals in our code, and it plans to make two mutations to those numbers. We can see in our
code that there is only one numeric literal, the value returned from ``func()`` on line 2:

.. literalinclude:: mod.1.py
    :linenos:
    :emphasize-lines: 2

So Cosmic Ray is going to mutate that number in two ways, running the test suite each time. 

The ``cr-report`` tool is useful for examining sessions, and it's main purpose is to give you summary reports after an
entire session has been executed, which we'll do in the next step.

Execution
=========

Now that you've initialized and baselined your session, it's time to start making mutants and testing them. We do this
with the ``exec`` command. ``exec`` looks in your session file, ``tutorial.sqlite``, for any mutations which were
detected in the ``init`` phase that don't yet have results. For each of these, it performs the specified mutation
and runs the test suite.

As we saw, we only have two mutations to make, and our test suite is very small. As a result the ``exec`` command will
run quite quickly:

.. code-block:: bash

    cosmic-ray exec tutorial.toml tutorial.sqlite

This should produce no output. 

.. note::

    The module and test suite for this tutorial are "toys" by design. As such, they run very quickly. Most real-world
    modules and test suites are much more substantial and require much longer to run. For example, if a test suite takes
    10 seconds to run and Cosmic Ray finds 1000 mutations, a full ``exec`` will take 10 x 1000 = 10,000 seconds, or
    about 2.7 hours. 

Committing before `exec`
------------------------

If you're using revision control with your code (you are, right?!), you should consider committing your changes before
running `exec`. While it's not strictly necessary to do this in simple cases, it's often important to commit if
you're using tools like `cr-http-workers` that rely on fetching code from a repository. 

Also, while Cosmic Ray is designed to be robust in the face of exceptions and crashes, there is always the possibility
that Cosmic Ray won't correctly undo a mutation. Remember, it makes mutations directly on disk, so if a mutation is
not correctly undone, and if you haven't committed your changes prior to testing, you run the risk of introducing
a mutation into you code accidentally.

Reporting the results
=====================

Assuming it ran correctly, we can now use ``cr-report`` to see the updated state of our session:

.. code-block:: bash

    cr-report tutorial.sqlite --show-pending

This time we see that both mutations were made, tests were run for each, and both were "killed":

.. code-block:: text

    [job-id] f168ef23dff24b75846a730858fe0111
    mod.py core/NumberReplacer 0
    worker outcome: normal, test outcome: killed
    [job-id] 929a563b613242b48dae0f2de74ad2af
    mod.py core/NumberReplacer 1
    worker outcome: normal, test outcome: killed
    total jobs: 2
    complete: 2 (100.00%)
    surviving mutants: 0 (0.00%)   

.. tip::

    You don't have to wait for ``exec`` to complete to generate a report. If you have a long-running session and want to
    see your progress, you can execute ``cr-report`` while ``cosmic-ray exec`` is running to view the progress the
    latter is making.

HTML reports
------------

You can also generate a handy HTML report with `cr-html`:

::

    cr-html tutorial.sqlite > report.html

You can then open ``report.html`` in your browser to see the details. One nice feature of these HTML reports is
that they show the actual mutation that was used.
