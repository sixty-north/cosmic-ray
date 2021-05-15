===================
Cosmic Ray Tutorial
===================

This tutorial will walk you through the steps needed to install, configure, and run Cosmic
Ray. 

Cloning Cosmic Ray
==================

The tutorial will use code and tests provided in the Cosmic Ray test suite, so you'll need to 
clone the Cosmic Ray git repository:

.. code-block::

    git clone https://github.com/sixty-north/cosmic-ray

This will create a directory called 'cosmic-ray' in the directory from which you run the command. For the rest of this
tutorial we'll refer to this new directory as ``REPO``.

.. note::

    When using ``REPO`` in example shell code, we'll use ``$REPO``. This means you can set the ``REPO`` environment
    variable and then run our commands verbatim in many shells. For example, if we want you to change
    to the ``REPO/tests`` directory, we'll use ``cd $REPO/tests``.

Installation
============

You'll also need to install Cosmic Ray and its dependencies. For this tutorial, you should install
the lastest released version with pip:

.. code-block::

    pip install cosmic-ray

You'll generally want to do this in a virtual environment, but it's not required.

Creating a configuration
========================

Before you do run any mutation tests, you need to create a *configuration file*.
A configuration is TOML file that specifies the modules you want to mutate, the
test scripts to use, and so forth. A configuration is used to create a session,
something we'll look at in the next section.

The ``new-config`` command
--------------------------

You can create a configuration by hand if you want. In fact, you'll generally
need to edit them by hand to get the exact configuration you need. But you can
create an initial configuration using the ``new-config`` command. This will ask
you a series of questions and construct a new configuration based on your
answers.

To create your config for this tutorial, do this:

.. code-block:: 

    cd $REPO/tests/resources/example_project
    cosmic-ray new-config tutorial.toml

This will ask you a series of questions. Anwer them like this:

.. code-block::

    [?] Top-level module path: adam
    [?] Python version (blank for auto detection): 
    [?] Test execution timeout (seconds): 10
    [?] Test command: python -m unittest tests
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

On line 2 we set the 'module-path' key to the string "adam":

.. literalinclude:: tutorial.toml.1
    :lines: 2
    :language: toml

This tells Cosmic Ray that we're going to be mutating the module - and in this case, the *package* - called "adam". Every
Cosmic Ray configuration refers to a single top-level module that will be mutated, and in this case we're telling Cosmic Ray
to mutate the "adam" module, contained in the "adam" directory.

On line 3 we tell Cosmic Ray which version of Python to use when mutating the code:

.. literalinclude:: tutorial.toml.1
    :lines: 3
    :language: toml

Normally you'll want to leave this blank as we do here. This instructs Cosmic Ray to use the version of the 
Python environment in which Cosmic Ray is executing. 

Line 4 tells Cosmic Ray the maximium amount of time to let a test run before it's considered a failure:

.. literalinclude:: tutorial.toml.1
    :lines: 4
    :language: toml

In this case, we're telling Cosmic Ray to kill a test if it runs longer than 10 seconds. This timeout is important because
some mutations can cause the tests to go into an infinite loop. Without timeout we'd never exit the test! It's important to 
set this timeout such that it's long enough for all legitimate tests.

Next, line 5 tells Cosmic Ray which modules to exclude from mutation:

.. literalinclude:: tutorial.toml.1
    :lines: 5
    :language: toml

In this case we're not excluding any, but there may be times when you need to skip certain modules, e.g. because 
you know that you don't have sufficient tests for them at the moment.

Line 6 is one of the most critical lines in the configuration. This tells Cosmic Ray how to run you test suite:

.. literalinclude:: tutorial.toml.1
    :lines: 6
    :language: toml

In this case, our test suite uses the standard `unittest testing framework
<https://docs.python.org/3/library/unittest.html>`_, and the tests are in the ``tests`` directory.

The last two lines tell Cosmic Ray which "distributor" to use:

.. literalinclude:: tutorial.toml.1
    :lines: 8-9
    :language: toml

A distributor controls how mutation-and-test jobs are assigned to one or more workers so that they can (potentitally)
run in parallel. In this case we're using the default 'local' distributor which only runs one mutation at a time. There
are other, more sophisticated distributors which we discuss elsewhere.

Create a session and run tests
==============================

Cosmic Ray uses a notion of *sessions* to encompass a full mutation testing
suite. Since mutation testing runs can take a long time, and since you might
need to stop and start them, sessions store data about the progress of a run.

Initializing a session
----------------------

The first step in a full testing run, then, is to initialize a session:

.. code-block::

    cosmic-ray init tutorial.toml tutorial.sqlite

.. note::

    This command prepares all the mutations that will later be applied to code.
    As such, its execution time is proportional to the amount of code and
    the code complexitly. You can expect about 15-30s per 1kloc.

This will create a database file called ``tutorial.sqlite``. There is a record in the database for each mutation that
Cosmic Ray will perform, and Cosmic Ray will associate testing results with these records as it executes.

Baselining
----------

Before running the full mutation suite, it's important to make sure that the test suite passes in the absence of any
mutations. If the test suite does *not* pass in the absence of mutations, then the results of the mutation testing are
essentially useless.

You can use the ``baseline`` command to check that the test suite passes on unmutated code:

.. code-block::

    cosmic-ray baseline --report tutorial.toml tutorial.sqlite

This should report that the tests pass:

.. code-block::

    Execution with no mutation works fine.

You'll also see that there is a new ``tutorial.baseline.sqlite`` database containing the results of the baselining.

.. tip::

    Only one baseline can be stored in the baseline database. If the execution failed
    and you fixed the environment without changing the source code, you
    can re-baseline it with ``--force`` option without the need to run ``init``
    again.


If this command succeeds, you can start executing tests with the ``exec``
command:

::

    cosmic-ray exec my_session.sqlite

Unless there are errors, this won't print anything.

.. Tip::
    Because this command executes the provided test suite for every mutation
    it selected, it will require many times more time to execute than the
    whole test suite. It can be killed at any point though and restarted
    while keeping the status of executed mutations between the runs.

View the results
----------------

Once the execution is complete (i.e., all mutations have been performed
and tested), you can see the results of your session with the
``cr-report`` command:

::

    cr-report my_session.sqlite

This will print out a bunch of information about the work that was
performed, including what kinds of mutants were created, which were
killed, and – chillingly – which survived.

.. Tip::
    You can execute ``cr-report`` while ``cosmic-ray exec`` is running to
    view the progress the latter is making.

You can also generate a handy HTML report with `cr-html`:

::

    cr-html my_session.sqlite > my_session.html

Or use the ``cr-rate`` command to return error if the survival rate rose above
a specified value:

::

    cr-rate --fail-over 20.5 my_session.sqlite

.. Tip::
    ``cr-rate`` can also calculate confidence intervals for the survival rate
    when the ``cosmic-ray exec`` hasn't finished yet.

A concrete example: running the ``adam`` unittests
--------------------------------------------------

Cosmic Ray includes a number of unit tests which perform mutations
against a simple package called ``adam``. As a way of test driving Cosmic
Ray, you can run these tests, too, like this:

::

    cd test_project
    cosmic-ray -v INFO init cosmic-ray.unittest.local.conf example-session.sqlite
    cosmic-ray -v INFO exec example-session.sqlite
    cr-report example-session.sqlite

In this case we're passing the ``-v INFO`` flag to the ``init`` and ``exec``
commands so that you can see what Cosmic Ray is doing. If everything goes
as expected, the ``cr-report`` command will report a 0% survival rate.
