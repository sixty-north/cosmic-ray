"Tests for the command line interface and return codes."

# pylint: disable=C0111,W0621,W0613

import contextlib
import io
import stat

from exit_codes import ExitCode
import pytest

import cosmic_ray.cli
import cosmic_ray.config
import cosmic_ray.modules
import cosmic_ray.plugins
import cosmic_ray.mutating


@pytest.fixture
def config_file(tmpdir):
    return str(tmpdir.join("config.toml"))


def _make_config(test_command="python -m unittest discover tests", timeout=100, engine="local"):
    return {
        "module-path": "foo.py",
        "timeout": timeout,
        "test-command": test_command,
        "execution-engine": {"name": engine},
        "exclude-modules": [],
        "cloning": {"method": "copy"},
    }


@pytest.fixture
def local_unittest_config(config_file):
    """Creates a valid config file for local, unittest-based execution, returning
    the path to the config.
    """
    with open(config_file, mode="wt") as handle:
        config = _make_config()
        config_str = cosmic_ray.config.serialize_config(config)
        handle.write(config_str)
    return config_file


@pytest.fixture
def lobotomize(monkeypatch):
    "Short-circuit some of CR's core functionality to make testing simpler."
    # This effectively prevent init from actually trying to scan the module in the config.
    monkeypatch.setattr(cosmic_ray.modules, "find_modules", lambda *args: [])

    # Make cosmic_ray.mutating.mutate_and_test just return a simple empty dict.
    monkeypatch.setattr(cosmic_ray.mutating, "mutate_and_test", lambda *args: {})


def test_invalid_command_line_returns_EX_USAGE():
    assert cosmic_ray.cli.main(["init", "foo"]) == 2


def test_non_existent_file_returns_EX_NOINPUT():
    assert cosmic_ray.cli.main(["exec", "foo.session"]) == ExitCode.NO_INPUT


@pytest.mark.skip("need to sort this API out")
def test_unreadable_file_returns_EX_PERM(tmpdir):
    p = tmpdir.ensure("bogus.session.sqlite")
    p.chmod(stat.S_IRUSR)
    assert cosmic_ray.cli.main(["exec", str(p.realpath())]) == ExitCode.NO_PERM


def test_new_config_success_returns_EX_OK(monkeypatch, config_file):
    monkeypatch.setattr(cosmic_ray.commands, "new_config", lambda *args: "")
    errcode = cosmic_ray.cli.main(["new-config", config_file])
    assert errcode == ExitCode.OK


# NOTE: We have integration tests for the happy-path for many commands, so we don't cover them explicitly here.


def test_config_success_returns_EX_OK(lobotomize, local_unittest_config, session):
    cosmic_ray.cli.main(["init", local_unittest_config, str(session)])

    cfg_stream = io.StringIO()
    with contextlib.redirect_stdout(cfg_stream):
        errcode = cosmic_ray.cli.main(["config", str(session)])
    assert errcode == ExitCode.OK

    with open(local_unittest_config, mode="rt") as handle:
        config_str = handle.read()
        orig_cfg = cosmic_ray.config.deserialize_config(config_str)
    stored_cfg = cosmic_ray.config.deserialize_config(cfg_stream.getvalue())
    assert orig_cfg == stored_cfg


def test_dump_success_returns_EX_OK(lobotomize, local_unittest_config, session):
    errcode = cosmic_ray.cli.main(["init", local_unittest_config, str(session)])
    assert errcode == ExitCode.OK

    errcode = cosmic_ray.cli.main(["dump", str(session)])
    assert errcode == ExitCode.OK


def test_operators_success_returns_EX_OK():
    assert cosmic_ray.cli.main(["operators"]) == ExitCode.OK


# def test_mutate_and_test_success_returns_EX_OK(lobotomize, local_unittest_config):
#     cmd = ["worker", "some_module", "core/ReplaceTrueWithFalse", "0", local_unittest_config]
#     assert cosmic_ray.cli.main(cmd) == ExitCode.OK
