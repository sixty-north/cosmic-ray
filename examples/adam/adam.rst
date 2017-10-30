Cosmic Ray example: Adam
------------------------

This example demonstrates how to use cosmic-ray to improve the testing suite
for a simple module called `adam`.

First run cosmic-ray on the so called 'bad' testing suite.

::

    cosmic-ray init cosmic-ray-bad_tests.conf bad_session
    cosmic-ray --verbose exec bad_session
    cosmic-ray dump bad_session | cr-report


You should end up with a series of mutants that have survived. This is because in
`test_adam_bad_tests.py` there are not enough tests to cover `adam.py`.

We add a couple of tests in `test_adam_good_tests.py` to ensure full coverage. Run
cosmic-ray again on the new testing suite.

::

    cosmic-ray init cosmic-ray-good_tests.conf good_session
    cosmic-ray --verbose exec good_session
    cosmic-ray dump good_session | cr-report
