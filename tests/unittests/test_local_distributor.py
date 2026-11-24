"Tests for cosmic_ray.distribution.local."

from types import SimpleNamespace

from cosmic_ray.config import ConfigDict
from cosmic_ray.distribution import local


def test_local_distributor_passes_the_memory_limit(monkeypatch):
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
