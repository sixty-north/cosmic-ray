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

For example, to create a new configuration in the file ``config.yml`` use this
command::

    cosmic-ray new-config config.yml

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
    test-command = "{python-executable} -m unittest discover tests"
    execution-engine.name = "local"

    [cosmic-ray.cloning]
    method = 'copy'
    commands = []

You can specify a great deal of information in a configuration file, controlling
things like the test execution, the execution engine, and so forth. It's
entirely likely that the configuration created by ``cosmic-ray new-config`` won't be
sufficient for your needs. Simply edit the config file to match your needs.

Create a session and run tests
------------------------------

Cosmic Ray uses a notion of *sessions* to encompass a full mutation testing
suite. Since mutation testing runs can take a long time, and since you might
need to stop and start them, sessions store data about the progress of a run.
The first step in a full testing run, then, is to initialize a session:

::

    cosmic-ray init config.toml my_session.sqlite

(Note that you don't have to use the names "config.toml" and "my_session.sqlite".
Any names will do.)

This will also create a database file called ``my_session.sqlite``. Once this is
created, you can start executing tests with the ``exec`` command:

::

    cosmic-ray exec my_session.sqlite

Unless there are errors, this won't print anything.

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

You can also generate a handy HTML report with `cr-html`:

::

    cr-html my_session.sqlite > my_session.html

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
