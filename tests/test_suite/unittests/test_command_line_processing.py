"Tests for the command line interface and return codes."

# pylint: disable=C0111,W0621,W0613

import contextlib
import io
import stat

import pytest

import cosmic_ray.cli
import cosmic_ray.config
import cosmic_ray.modules
import cosmic_ray.plugins
import cosmic_ray.worker
from cosmic_ray.exit_codes import ExitCode
from cosmic_ray.work_item import TestOutcome


@pytest.fixture
def config_file(tmpdir):
    return str(tmpdir.join('config.toml'))


def _make_config(test_command='python -m unittest discover tests',
                 baseline=None,
                 timeout=100,
                 engine='local'):
    timeout_type = 'timeout' if baseline is None else 'baseline'
    timeout_val = timeout if baseline is None else baseline
    return {
        'module-path': 'foo.py',
        timeout_type: timeout_val,
        'test-command': test_command,
        'execution-engine': {'name': engine},
        'exclude-modules': []
    }


@pytest.fixture
def local_unittest_config(config_file):
    """Creates a valid config file for local, unittest-based execution, returning
    the path to the config.
    """
    with open(config_file, mode='wt') as handle:
        config = _make_config()
        config_str = cosmic_ray.config.serialize_config(config)
        handle.write(config_str)
    return config_file


@pytest.fixture(params=['-1', '0'])
def invalid_baseline_config(request, config_file):
    "Creates a config file with an invalid baseline."
    with open(config_file, mode='wt') as handle:
        config = _make_config(baseline=int(request.param))
        config_str = cosmic_ray.config.serialize_config(config)
        handle.write(config_str)
    return config_file


@pytest.fixture
def lobotomize(monkeypatch):
    "Short-circuit some of CR's core functionality to make testing simpler."
    # This effectively prevent init from actually trying to scan the module in the config.
    monkeypatch.setattr(cosmic_ray.modules, 'find_modules', lambda *args: [])

    # Make cosmic_ray.worker.worker just return a simple empty dict.
    monkeypatch.setattr(cosmic_ray.worker, 'worker', lambda *args: {})


def test_invalid_command_line_returns_EX_USAGE():
    assert cosmic_ray.cli.main(['init', 'foo']) == ExitCode.Usage


def test_non_existent_file_returns_EX_NOINPUT():
    assert cosmic_ray.cli.main(['exec', 'foo.session']) == ExitCode.NoInput


@pytest.mark.skip('need to sort this API out')
def test_unreadable_file_returns_EX_PERM(tmpdir):
    p = tmpdir.ensure('bogus.session.sqlite')
    p.chmod(stat.S_IRUSR)
    assert cosmic_ray.cli.main(['exec', str(p.realpath())]) == ExitCode.NoPerm


def test_baseline_failure_returns_2(monkeypatch, local_unittest_config):
    monkeypatch.setattr(cosmic_ray.testing, 'run_tests',
                        lambda *args: (TestOutcome.KILLED, ''))

    errcode = cosmic_ray.cli.main(['baseline', local_unittest_config])
    assert errcode == 2


def test_baseline_success_returns_EX_OK(monkeypatch, local_unittest_config):
    monkeypatch.setattr(cosmic_ray.testing, 'run_tests',
                        lambda *args: (TestOutcome.SURVIVED, ''))

    errcode = cosmic_ray.cli.main(['baseline', local_unittest_config])
    assert errcode == ExitCode.OK


def test_new_config_success_returns_EX_OK(monkeypatch, config_file):
    monkeypatch.setattr(cosmic_ray.commands, 'new_config', lambda *args: '')
    errcode = cosmic_ray.cli.main(['new-config', config_file])
    assert errcode == ExitCode.OK


def test_init_with_invalid_baseline_returns_EX_CONFIG(invalid_baseline_config,
                                                      session):
    errcode = cosmic_ray.cli.main(
        ['init', invalid_baseline_config,
         str(session)])
    assert errcode == ExitCode.Config


# NOTE: We have integration tests for the happy-path for many commands, so we don't cover them explicitly here.


def test_config_success_returns_EX_OK(lobotomize, local_unittest_config,
                                      session):
    cosmic_ray.cli.main(['init', local_unittest_config, str(session)])

    cfg_stream = io.StringIO()
    with contextlib.redirect_stdout(cfg_stream):
        errcode = cosmic_ray.cli.main(['config', str(session)])
    assert errcode == ExitCode.OK

    with open(local_unittest_config, mode='rt') as handle:
        config_str = handle.read()
        orig_cfg = cosmic_ray.config.deserialize_config(config_str)
    stored_cfg = cosmic_ray.config.deserialize_config(cfg_stream.getvalue())
    assert orig_cfg == stored_cfg


def test_dump_success_returns_EX_OK(lobotomize, local_unittest_config,
                                    session):
    errcode = cosmic_ray.cli.main(
        ['init', local_unittest_config,
         str(session)])
    assert errcode == ExitCode.OK

    errcode = cosmic_ray.cli.main(['dump', str(session)])
    assert errcode == ExitCode.OK


def test_operators_success_returns_EX_OK():
    assert cosmic_ray.cli.main(['operators']) == ExitCode.OK


def test_worker_success_returns_EX_OK(lobotomize, local_unittest_config):
    cmd = [
        'worker', 'some_module', 'core/ReplaceTrueWithFalse', '0',
        local_unittest_config
    ]
    assert cosmic_ray.cli.main(cmd) == ExitCode.OK
