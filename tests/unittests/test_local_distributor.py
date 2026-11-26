"Tests for cosmic_ray.distribution.local."

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import cosmic_ray.testing as testing
from cosmic_ray.config import ConfigDict, ConfigValueError
from cosmic_ray.distribution import local


def test_local_distributor_passes_the_memory_limit(monkeypatch):
    monkeypatch.setattr(testing, "sys", SimpleNamespace(platform="linux"))
    calls = []
    monkeypatch.setattr(local, "mutate_and_test", lambda **kwargs: calls.append(kwargs) or "result")
    work = [SimpleNamespace(job_id="job", mutations=[])]
    done = []
    local.LocalDistributor()(work, "pytest", 5, ConfigDict({"memory-limit-mb": 512}), lambda *a: done.append(a))
    assert calls[0]["memory_limit_mb"] == 512
    assert done == [("job", "result")]


def test_local_distributor_has_no_memory_limit_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(local, "mutate_and_test", lambda **kwargs: calls.append(kwargs))
    local.LocalDistributor()([SimpleNamespace(job_id="job", mutations=[])], "pytest", 5, ConfigDict(), lambda *a: None)
    assert calls[0]["memory_limit_mb"] is None


@pytest.mark.parametrize(
    "platform, limit, message",
    [
        ("darwin", 200, "supported only"),
        ("freebsd14", 200, "supported only"),
        *[("linux", limit, "positive integer") for limit in (0, -1, True, 1.5, "200")],
    ],
)
def test_local_rejects_limits_before_consuming_work(monkeypatch, platform, limit, message):
    monkeypatch.setattr(testing, "sys", SimpleNamespace(platform=platform))
    mutate = Mock()
    completed = Mock()
    monkeypatch.setattr(local, "mutate_and_test", mutate)

    def pending():
        pytest.fail("Invalid limits must be rejected before consuming work")
        yield

    with pytest.raises(ConfigValueError, match=message):
        local.LocalDistributor()(pending(), "unused", 5, ConfigDict({"memory-limit-mb": limit}), completed)
    mutate.assert_not_called()
    completed.assert_not_called()
