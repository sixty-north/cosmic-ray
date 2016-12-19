# This runs the "adam" tests, returning 0 if all mutants are killed, or 1 if
# there's a survivor.

cosmic-ray load cosmic-ray.unittest.dist.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate adam_tests.unittest.dist`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report adam_tests.unittest.dist
    exit 1
fi

cosmic-ray load cosmic-ray.unittest.local.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate adam_tests.unittest.local`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report adam_tests.unittest.local
    exit 1
fi

cosmic-ray load cosmic-ray.pytest.dist.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate adam_tests.pytest.dist`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report adam_tests.pytest.dist
    exit 1
fi

cosmic-ray load cosmic-ray.pytest.local.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate adam_tests.pytest.local`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report adam_tests.pytest.local
    exit 1
fi

cosmic-ray load cosmic-ray.nosetest.dist.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate adam_tests.nosetest`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report adam_tests.nosetest.dist
    exit 1
fi

cosmic-ray load cosmic-ray.nosetest.local.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate adam_tests.nosetest`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report adam_tests.nosetest.local
    exit 1
fi

# Run import tests
cosmic-ray load cosmic-ray.import.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate import_tests`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report import_tests
    exit 1
fi

# Run tests for empty __init__.py
cosmic-ray load cosmic-ray.empty.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray survival-rate empty.unittest`
if [ $RESULT != 0.00 ]; then
    cosmic-ray report empty.unittest
    exit 1
fi

# Run failing baseline tests
cosmic-ray load cosmic-ray.baseline_fail.conf
if [ $? != 2 ]; then
    echo "baseline didn't fail"
    exit 1
fi

exit 0
