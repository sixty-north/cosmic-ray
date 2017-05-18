# This runs the "adam" tests, returning 0 if all mutants are killed, or 1 if
# there's a survivor.

TEST_CONFIGS="unittest.dist unittest.local pytest.dist pytest.local nosetest.dist nosetest.dist"
for CONFIG in $TEST_CONFIGS; do
    echo $CONFIG
    cosmic-ray load cosmic-ray.$CONFIG.conf
    if [ $? != 0 ]; then exit 1; fi
    RESULT=`cosmic-ray dump adam_tests.$CONFIG | cr-rate`
    if [ $RESULT != 0.00 ]; then
        cosmic-ray dump adam_tests.$CONFIG | cr-format
        exit 1
    fi
done

# Run import tests
cosmic-ray load cosmic-ray.import.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray dump import_tests | cr-rate`
if [ $RESULT != 0.00 ]; then
    cosmic-ray dump import_tests | cr-format
    exit 1
fi

# Run tests for empty __init__.py
cosmic-ray load cosmic-ray.empty.conf
if [ $? != 0 ]; then exit 1; fi
RESULT=`cosmic-ray dump empty.unittest | cr-rate`
if [ $RESULT != 0.00 ]; then
    cosmic-ray dump empty.unittest | cr-format
    exit 1
fi

# Run failing baseline tests
cosmic-ray load cosmic-ray.baseline_fail.conf
if [ $? != 2 ]; then
    echo "baseline didn't fail"
    exit 1
fi

exit 0
