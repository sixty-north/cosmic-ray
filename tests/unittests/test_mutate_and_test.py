"Tests for worker."

from pathlib import Path
from types import SimpleNamespace

import pytest

import cosmic_ray.testing as testing
from cosmic_ray.config import ConfigValueError
from cosmic_ray.mutating import _make_diff, mutate_and_test
from cosmic_ray.work_item import MutationSpec, WorkResult, WorkerOutcome


def test_no_test_return_value(path_utils, data_dir):
    with path_utils.excursion(data_dir):
        result = mutate_and_test(
            [
                MutationSpec(
                    Path("a/b.py"),
                    "core/ReplaceTrueWithFalse",
                    100,
                    # TODO: As in other places, these are placeholder position values. How can we not have to provide them?
                    (0, 0),
                    (0, 1),
                )
            ],
            "python -m unittest tests",
            1000,
        )

        expected = WorkResult(
            output=None,
            test_outcome=None,
            diff=None,
            worker_outcome=WorkerOutcome.NO_TEST,
        )
        assert result == expected


def test_private_make_diff():
    result = _make_diff("return True\n", "return False\n", Path("adam_1.py"))

    assert result == [
        "--- mutation diff ---",
        "--- a/adam_1.py",
        "+++ b/adam_1.py",
        "@@ -1,2 +1,2 @@",
        "-return True",
        "+return False",
        " ",
    ]


def test_unsupported_memory_limit_is_rejected_before_mutation(monkeypatch):
    monkeypatch.setattr(testing, "sys", SimpleNamespace(platform="darwin"))

    def mutations():
        pytest.fail("Unsupported limits must not apply any mutations")
        yield

    with pytest.raises(ConfigValueError, match="supported only"):
        mutate_and_test(mutations(), "unused", 5, memory_limit_mb=200)
