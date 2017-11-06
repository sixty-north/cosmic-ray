#!/bin/sh

# Stop on errors.
set -e

# This runs the "adam" tests, returning 0 if all mutants are killed, or 1 if
# there's a survivor.
TEST_CONFIGS="unittest.celery3 unittest.local pytest.celery3 pytest.local nosetest.celery3 nosetest.celery3"
for CONFIG in $TEST_CONFIGS; do
    echo "$CONFIG"
    SESSION=adam_tests.$CONFIG
    cosmic-ray init cosmic-ray.$CONFIG.conf $SESSION
    cosmic-ray exec $SESSION
    RESULT="$(cosmic-ray dump "$SESSION" | cr-rate)"
    if [ "$RESULT" != 0.00 ]; then
        cosmic-ray dump "$SESSION" | cr-format
        exit 1
    fi
done

# Run import tests
cosmic-ray init cosmic-ray.import.conf import_tests
RESULT="$(cosmic-ray dump import_tests | cr-rate)"
if [ "$RESULT" != 0.00 ]; then
    cosmic-ray dump import_tests | cr-format
    exit 1
fi

# Run tests for empty __init__.py
cosmic-ray init cosmic-ray.empty.conf empty.unittest
RESULT="$(cosmic-ray dump empty.unittest | cr-rate)"
if [ "$RESULT" != 0.00 ]; then
    cosmic-ray dump empty.unittest | cr-format
    exit 1
fi

# Run failing baseline tests
if cosmic-ray init cosmic-ray.baseline_fail.conf baseline_fail; then
    echo "baseline didn't fail"
    exit 1
fi

exit 0
