Test Runner
===========

In Cosmic Ray we use test runners to allow us to run any type of test
that your project uses.

Implementation details
----------------------

Cosmic Ray uses various packages that can be found under
plugins/test-runners.

Cosmic Ray comes with out of the box supported plugins for:
1. unittest
2. pytest
3. nose
4. nose2

Each test runner is ultimately a subclass of
``cosmic_ray.testing.TestRunner``.

Each mutation will invoke another instance of the test runner, in order
to run all tests for this specific mutant.

Implementing a test runner
--------------------------

To implement a new test runner you need to create a new package.
An example is provided at the end.

The test runner must inherit TestRunner.
Test Runner has 3 methods:
1. __init__
2. _run
3. __call__

__init__ is already implemented as part of TestRunner, and provides
initialization for test_args.

The abstract method is _run:
It should discover all the tests that it should run and returns the results.
The results are returned as a (success, result)
tuple. `success` is a boolean indicating if the tests
passed. `result` is any object that is appropriate to provide
more information about the success/failure of the tests.

Test Runners are provided as plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cosmic Ray is designed to be extended with arbitrary test runners provided
by users. It dynamically discovers tets runners at runtime using the
``stevedore`` plugin system which relies on the ``setuptools``
``entry_points`` concept. To make a new plugin available to Cosmic Ray
you need to create a ``cosmic_ray.test_runners`` entry point; this is
generally done in ``setup.py``. We'll show an example of how to do this
later.

A full example: ``AnotherRunner``
---------------------------------

One of the plugins bundled with Cosmic Ray is
``cosmic_ray.testing.unittest_runner``.
This test runner uses unittest package. It looks for test cases using
the unittest package discover routine.
To demonstrate how to create a test runner, we'll step through how to
create that test runner in a new package called ``cosmic_ray_another_runner``.

Creating the operator class
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The initial layout for our package is like this:

::

    setup.py
    cosmic_ray_another_runner/
      __init__.py
      version.py

``__init__.py`` is empty and ``setup.py`` has very minimal content:

::

    from setuptools import setup

    setup(
        name='cosmic_ray_another_runner',
        version='0.1.0',
        }
    )

The first thing we need to do is create a new Python source file to hold
our new test_runner. Create a file named ``runner.py`` in the
``another_runner`` directory. It has the following contents:

::
    import unittest
    from itertools import chain

    from cosmic_ray.testing.test_runner import TestRunner


    class AnotherRunner(TestRunner):

        def _run(self):
            suite = unittest.TestLoader().discover(self.test_args)
            result = unittest.TestResult()
            result.failfast = True
            suite.run(result)

            return (
                result.wasSuccessful(),
                [r[1] for r in chain(result.errors, result.failures)])

Let's step through this line-by-line. We first import ``unittest`` because
we'll need to use a test runner and discover the test cases.

::

    import unittest

Next we import a utility to help us aggregate results.

::
   from itertools import chain

Next we import the ``TestRunner`` base class.

::

    from cosmic_ray.testing.test_runner import TestRunner

We define our new test runner by creating a subclass of ``TestRunner`` called
``AnotherRunner``:

::

    class AnotherRunner(TestRunner):

In order for it to provide the functionality, it should detect test cases
and return a tuple, which consist of boolean indicating if it succeed to run
and any object which can be used to describe the tests results.

::

        def _run(self):
            suite = unittest.TestLoader().discover(self.test_args)
            result = unittest.TestResult()
            result.failfast = True
            suite.run(result)

            return (
                result.wasSuccessful(),
                [r[1] for r in chain(result.errors, result.failures)])

That's all there is to it. This test runner is now ready to be
applied to any code you want to test.

However, before it can really be used, you need to make it available as
a plugin.

Creating the plugin
~~~~~~~~~~~~~~~~~~~

In order to make your test runner available to Cosmic Ray as a plugin, you
need to define a new ``cosmic_ray.test_runners`` entry point. This is
generally done through ``setup.py``, which is what we'll do here.

Modify ``setup.py`` with a new ``entry_points`` argument to ``setup()``:

::

    setup(
        . . .
        entry_points={
            'cosmic_ray.test_runners': [
                'another_runner = cosmic_ray_another_runner.runner:Runner'
            ]
        })

Now when Cosmic Ray queries the ``cosmic_ray.test_runners`` entry point it
will see your test runner along with all of the others.
