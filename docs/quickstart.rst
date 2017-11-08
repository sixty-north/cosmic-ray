Quickstart
==========

If you just want to get down to the business of finding and killing
mutants, you still need to set a few things up.

Create a session and run tests
------------------------------

Cosmic Ray uses a notion of *sessions* to encompass a full mutation testing
suite. Since mutation testing runs can take a long time, and since you might
need to stop and start them, sessions store data about the progress of a run.
The first step in a full testing run, then, is to initialize a session:

::

    cosmic-ray init config.yml my_session

If ``config.yml`` doesn't exist (which it won't initially) this will ask you a
series of questions to help create it. (Note that you don't have to use the
names "config.yml" and "my_session". Any names will do.)

This will also create a database file called ``my_session.json``. Once this is
created, you can start executing tests with the ``exec`` command:

::

    cosmic-ray exec my_session

Unless there are errors, this won't print anything.

Configuration file
~~~~~~~~~~~~~~~~~~

In the step above the call to ``cosmic-ray init`` helped you create a
*configuration file*. A configuration is YAML file that specifies the modules
you want to mutate, the test scripts to use, and so forth. As you did above, you
use a configuration to create a session.

Here's a simple example of a configuration file which uses ``unittest`` for
testing:

.. code:: yaml

    # config.yml

    module: <the top-level module you want to test>

    baseline: 10

    exclude-modules:

    test-runner:
      name: unittest
      args: <the directory containing your tests>

    execution-engine:
      name: local

You can specify a great deal of information in a configuration file, controlling
things like the test runner, execution engine, test paths, and so forth. It's
entirely likely that the configuration created by ``cosmic-ray init`` won't be
sufficient for your needs. As you make changes to your configuration, you can
generate new sessions from it by rerunning ``cosmic-ray init``; if this command
sees an existing configuration, it will use that instead of creating a new one.

View the results
----------------

Once the execution is complete (i.e., all mutations have been performed
and tested), you can see the results of your session with the
``cr-report`` command:

::

    cosmic-ray dump  my_session | cr-report

This will print out a bunch of information about the work that was
performed, including what kinds of mutants were created, which were
killed, and – chillingly – which survived.

A concrete example: running the ``adam`` unittests
--------------------------------------------------

Cosmic Ray includes a number of unit tests which perform mutations
against a simple module called ``adam``. As a way of test driving Cosmic
Ray, you can run these tests, too, like this:

::

    cd test_project
    cosmic-ray init cosmic-ray.unittest.local.conf example-session
    cosmic-ray --verbose exec example-session
    cosmic-ray dump example-session | cr-report

In this case we're passing the ``--verbose`` flag to the ``exec``
command so that you can see what Cosmic Ray is doing. If everything goes
as expected, the ``cr-report`` command will report a 0% survival rate.
