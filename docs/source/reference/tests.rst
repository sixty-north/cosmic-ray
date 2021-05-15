Tests
=====

Cosmic Ray has a number of test suites to help ensure that it works. To
install the necessary dependencies for testing, run:

::

    pip install -e .[dev,test]

``pytest`` suite
----------------

The first suite is a `pytest <http://pytest.org/>`__ test suite that
validates some if its internals. You can run that like this:

::

    pytest tests/test_suite

The "adam" tests
----------------

There is also a set of tests which verify the various mutation
operators. These tests comprise a specially prepared body of code,
``adam.py``, and a full-coverage test-suite. The idea here is that
Cosmic Ray should be 100% lethal against the mutants of ``adam.py`` or
there's a problem.

We have "adam" configurations for each of the
test-runner/execution-engine combinations. For example, the
configuration which uses ``unittest`` and the ``local`` execution
engine is in ``test_project/cosmic-ray.unittest.local.conf``.

To run an "adam" test, first switch to the ``test_project`` directory:

::

    cd tests/example_project

Then initialize a new session using one of the configurations. Here's an
example using the ``pytest``/``local`` configuration:

::

    cosmic-ray init cosmic-ray.pytest.local.conf pytest-local.sqlite

(Note that if you were going to use the ``celery4`` engine instead, you
need to make sure that celery workers were running.)

Execute the session like this:

::

    cosmic-ray exec pytest-local.sqlite

Finally, view the results of this test with ``dump`` and ``cr-report``:

::

    cr-report pytest-local.sqlite

You should see a 0% survival rate at the end of the report.

The full test suite
-------------------

While the "adam" tests verify the various mutation operators in Cosmic
Ray, the full test suite comprises a few more tests for other behaviors
and functionality. To run all of these tests, it's often simplest to use tox. Just run::

    $ tox

at the root of the project.
