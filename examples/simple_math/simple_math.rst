.. _examples-simple_math:

Improving the tests for a simple module
---------------------------------------

This example demonstrates how to use cosmic-ray to improve the testing
suite for a module called ``simple_math``.

::
    def mult_by_2(x):
        return x + x

    def square(x):
        return x*x

    def cube(x):
        return x*x*x

    def is_positive(x):
        return x > 0


First run cosmic-ray on the so called 'bad' testing suite.

::

    cosmic-ray init cosmic-ray-bad_tests.conf bad_session
    cosmic-ray --verbose exec bad_session
    cosmic-ray dump bad_session | cr-report

You should end up with a series of mutants that have survived. This is because in
``test_simple_math_bad.py`` there are not enough tests to cover ``simple_math.py``.

We add a couple of tests in ``test_simple_good_tests.py`` to ensure full coverage. Run
cosmic-ray again on the new testing suite.

::

    cosmic-ray init cosmic-ray-good_tests.conf good_session
    cosmic-ray --verbose exec good_session
    cosmic-ray dump good_session | cr-report

You should now get 0% survival rate for the mutants (yay!). This means that you
have a robust testing suite.
