"Tests for the command line interface and return codes."

import io
import os
import stat

import pytest
import yaml

import cosmic_ray.cli
import cosmic_ray.modules
import cosmic_ray.plugins
import cosmic_ray.util
import cosmic_ray.worker
from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.work_record import WorkRecord


@pytest.fixture
def config_file(tmpdir):
    return str(tmpdir.join('config.yml'))


@pytest.fixture
def session_file(tmpdir):
    """A session file name.
    """
    return str(tmpdir.join('session.json'))


def _make_config(test_runner='unittest',
                 test_args='tests',
                 baseline='10',
                 engine='local'):
    return '''module: foo

baseline: {baseline}

exclude-modules:

test-runner:
  name: {test_runner}
  args: {test_args}

execution-engine:
  name: {engine}
'''.format(test_runner=test_runner,
           test_args=test_args,
           baseline=baseline,
           engine=engine)


@pytest.fixture
def local_unittest_config(config_file):
    """Creates a valid config file for local, unittest-based execution, returning
    the path to the config.
    """
    with open(config_file, mode='wt') as handle:
        handle.write(_make_config())
    return config_file


@pytest.fixture(params=['-1', '', '0'])
def invalid_baseline_config(request, config_file):
    "Creates a config file with an invalid baseline."
    with open(config_file, mode='wt') as handle:
        handle.write(_make_config(baseline=request.param))
    return config_file


@pytest.fixture
def lobotomize(monkeypatch):
    "Short-circuit some of CR's core functionality to make testing simpler."
    # This effectively prevent init from actually trying to scan the module in the config.
    monkeypatch.setattr(cosmic_ray.modules, 'find_modules', lambda *args: [])

    # Make cosmic_ray.worker.worker just return a simple empty dict.
    monkeypatch.setattr(cosmic_ray.worker, 'worker', lambda *args: {})


def test_invalid_command_line_returns_EX_USAGE():
    assert cosmic_ray.cli.main(['init', 'foo']) == os.EX_USAGE


def test_non_existent_file_returns_EX_NOINPUT():
    assert cosmic_ray.cli.main(['exec', 'foo.session']) == os.EX_NOINPUT


def test_unreadable_file_returns_EX_PERM(tmpdir):
    p = tmpdir.ensure('bogus.session.json')
    p.chmod(stat.S_IRUSR)
    assert cosmic_ray.cli.main(['exec', str(p.realpath())]) == os.EX_NOPERM


def test_baseline_failure_returns_2(monkeypatch, local_unittest_config, session_file):
    def killed_mutant(*args):
        "Simulates a test run where a the tests fails."
        def inner():
            return WorkRecord(test_outcome=TestOutcome.KILLED,
                              data=[])
        return inner

    monkeypatch.setattr(cosmic_ray.plugins, 'get_test_runner', killed_mutant)

    errcode = cosmic_ray.cli.main(['baseline', local_unittest_config])
    assert errcode == 2


def test_baseline_success_returns_EX_OK(monkeypatch, local_unittest_config, session_file):
    def surviving_mutant(*args):
        "Simulates a test run where a the tests succeed."
        def inner():
            return WorkRecord(test_outcome=TestOutcome.SURVIVED,
                              data=[])
        return inner

    monkeypatch.setattr(cosmic_ray.plugins, 'get_test_runner', surviving_mutant)

    errcode = cosmic_ray.cli.main(['baseline', local_unittest_config])
    assert errcode == os.EX_OK


def test_new_config_success_returns_EX_OK(monkeypatch, config_file):
    monkeypatch.setattr(cosmic_ray.commands, 'new_config', lambda *args: '')
    errcode = cosmic_ray.cli.main(['new-config', config_file])
    assert errcode == os.EX_OK


def test_init_with_invalid_baseline_returns_EX_CONFIG(invalid_baseline_config, session_file):
    errcode = cosmic_ray.cli.main(['init', invalid_baseline_config, session_file])
    assert errcode == os.EX_CONFIG

# NOTE: We have integration tests for the happy-path for many commands, so we don't cover them explicitly here.


def test_config_success_returns_EX_OK(lobotomize, local_unittest_config, session_file):
    cosmic_ray.cli.main(['init', local_unittest_config, session_file])

    cfg_stream = io.StringIO()
    with cosmic_ray.util.redirect_stdout(cfg_stream):
        errcode = cosmic_ray.cli.main(['config', session_file])
    assert errcode == os.EX_OK

    with open(local_unittest_config, mode='rt') as handle:
        orig_cfg = yaml.load(handle)
    stored_cfg = yaml.load(cfg_stream.getvalue())
    assert orig_cfg == stored_cfg


def test_dump_success_returns_EX_OK(lobotomize, local_unittest_config, session_file):
    cosmic_ray.cli.main(['init', local_unittest_config, session_file])

    errcode = cosmic_ray.cli.main(['dump', session_file])
    assert errcode == os.EX_OK


def test_counts_success_returns_EX_OK(lobotomize, local_unittest_config):
    assert cosmic_ray.cli.main(['counts', local_unittest_config]) == os.EX_OK


def test_test_runners_success_returns_EX_OK():
    assert cosmic_ray.cli.main(['test-runners']) == os.EX_OK


def test_operators_success_returns_EX_OK():
    assert cosmic_ray.cli.main(['operators']) == os.EX_OK


def test_worker_success_returns_EX_OK(lobotomize, local_unittest_config):
    assert cosmic_ray.cli.main(['worker', 'some_module', 'remove_decorator', '0', local_unittest_config]) == os.EX_OK
