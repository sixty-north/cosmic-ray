Quickstart
==========

If you just want to get down to the business of finding and killing mutants, you
still need to set a few things up.

Configurations
--------------

Before you do run any mutation tests, you need to create a *configuration file*.
A configuration is TOML file that specifies the modules you want to mutate, the
test scripts to use, and so forth. A configuration is used to create a session,
something we'll look at in the next section.

You can create a configuration by hand if you want. In fact, you'll generally
need to edit them by hand to get the exact configuration you need. But you can
create an initial configuration using the ``new-config`` command. This will ask
you a series of questions and construct a new configuration based on your
answers.

For example, to create a new configuration in the file ``config.toml`` use this
command::

    cosmic-ray new-config config.toml

Example configuration
~~~~~~~~~~~~~~~~~~~~~

Here's a simple example of a configuration file which uses ``unittest`` for
testing:

.. code:: ini

    # config.toml
    [cosmic-ray]
    module-path = "adam.py"
    python-version = ""
    timeout = 10
    exclude-modules = []
    test-command = "python -m unittest discover tests"
    distributor.name = "local"

You can specify a great deal of information in a configuration file, controlling
things like the test execution, the execution engine, and so forth. It's
entirely likely that the configuration created by ``cosmic-ray new-config`` won't be
sufficient for your needs. Simply edit the config file to match your needs.
See :ref:`Test suite<test_suite>` for explanations of some of those
configuration options.

Create a session and run tests
------------------------------

Cosmic Ray uses a notion of *sessions* to encompass a full mutation testing
suite. Since mutation testing runs can take a long time, and since you might
need to stop and start them, sessions store data about the progress of a run.
The first step in a full testing run, then, is to initialize a session:

::

    cosmic-ray init config.toml my_session.sqlite

.. Tip::
    You don't have to use the names ``config.toml`` and ``my_session.sqlite``.
    Any names will do.

.. Note::
    This command prepares all the mutations that will later be applied to code.
    As such, its execution time is proportional to the amount of code and
    the code complexitly. You can expect about 15-30s per 1kloc.

This will also create a database file called ``my_session.sqlite``.

To verify that the environment is sane (that the test suite passes when it is
executed by cosmic-ray), you can run the ``baseline`` command:

::

    cosmic-ray baseline --report my_session.sqlite

.. Tip::
    Only one baseline can be stored in the database. If the execution failed
    and you fixed the environment without changing the source code, you
    can re-execute it with ``--force`` option without the need to run ``init``
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
