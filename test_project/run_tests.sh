# This runs the "adam" tests, returning 0 if all mutants are killed, or 1 if
# there's a survivor.

set -e

cosmic-ray load cosmic-ray.unittest.conf
# cosmic-ray report adam_tests.unittest
RESULT=`cosmic-ray survival-rate adam_tests.unittest`
if [ $RESULT != 0.00 ]; then exit 1; fi

cosmic-ray load cosmic-ray.pytest.conf
# cosmic-ray report adam_tests.pytest
RESULT=`cosmic-ray survival-rate adam_tests.pytest`
if [ $RESULT != 0.00 ]; then exit 1; fi

exit 0
