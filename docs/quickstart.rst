Quickstart
==========

If you just want to get down to the business of finding and killing
mutants, you still need to set a few things up.

Create a configuration
----------------------

A configuration is YAML file that specifies the modules you want to
mutate, the test scripts to use, and so forth. You use a configuration
to create a session. Here's a simple example using ``unittest`` for
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

Save this into a file named "config.yml".

Create a session and run tests
------------------------------

Now you're ready to start killing mutants! Cosmic Ray uses a notion of
*sessions* to encompass a full mutation testing suite. Since mutation
testing runs can take a long time, and since you might need to stop and
start them, sessions store data about the progress of a run. The first
step in a full testing run, then, is to initialize a session:

::

    cosmic-ray init config.yml my_session

This will create a database file called ``my_session.json``. Once this
is created, you can start executing tests with the ``exec`` command:

::

    cosmic-ray exec my_session

Unless there are errors, this won't print anything.

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

See :ref:`examples-simple_math` for a step-by-step guide for
dealing with tests that have a non-zero mutation survival rate.
