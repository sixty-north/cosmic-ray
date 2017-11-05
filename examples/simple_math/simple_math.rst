.. _examples-simple_math:

Improving the tests for a simple module
---------------------------------------

This example demonstrates how to use cosmic-ray to improve the testing
suite for a module called ``simple_math``. The code is located in the
``examples/simple_math`` directory.

::

    # examples/simple_math/simple_math.py

    def mult_by_2(x):
        return x + x

    def square(x):
        return x*x

    def cube(x):
        return x*x*x

    def is_positive(x):
        return x > 0


We would like to measure the performance of a testing suite,
``test_simple_math_bad.py``, with intention to improve it.
First run cosmic-ray on the so-called 'bad' testing suite.

::

    cosmic-ray init cosmic-ray-bad_tests.conf bad_session
    cosmic-ray --verbose exec bad_session
    cosmic-ray dump bad_session | cr-report

You should end up with at least one mutant that survives. This is because the test
``test_mult_by_2`` from ``test_simple_math_bad.py`` still passes when we replace
``x + x`` with ``x * x`` or ``x ** x``, as they all return the same answer, ``4``,
when ``x = 2``.

Here is the bad test that lets the mutant(s) survive:

::
    # examples/simple_math/test_simple_math_bad.py

    def test_mult_by_2():
        assert mult_by_2(2) == 4

To fix this bad test, we decorate it so that a range
of values of `x` are tested:

::
    # examples/simple_math/test_simple_math_good.py

    @pytest.mark.parametrize('x', range(-5, 5))
    def test_mult_by_2(x):
        assert mult_by_2(x) == x * 2

Now this test should fail for all the mutations to the underlying
function ``mult_by_2``, which is what we want it to do.
Run cosmic-ray again on the new testing suite, ``test_simple_math_good.py``

::

    cosmic-ray init cosmic-ray-good_tests.conf good_session
    cosmic-ray --verbose exec good_session
    cosmic-ray dump good_session | cr-report

You should now get 0% survival rate for the mutants. This means your
testing suite is now more robust.
