"Tests for the command line interface and return codes."

# pylint: disable=C0111,W0621,W0613

import stat

import pytest

from exit_codes import ExitCode
from pathlib import Path
import cosmic_ray.cli
import cosmic_ray.config
import cosmic_ray.modules
import cosmic_ray.mutating
import cosmic_ray.plugins
import cosmic_ray.commands
from cosmic_ray.config import ConfigDict
from cosmic_ray.work_db import WorkDB,use_db
from cosmic_ray.commands.execute import execute
from cosmic_ray.work_item import WorkItem,MutationSpec

@pytest.fixture
def config_file(tmpdir):
    return str(tmpdir.join("config.toml"))


def _make_config(test_command="python -m unittest discover tests", timeout=100, distributor="local"):
    return {
        "module-path": "foo.py",
        "timeout": timeout,
        "test-command": test_command,
        "distributor": {"name": distributor},
        "excluded-modules": [],
    }


@pytest.fixture
def local_unittest_config(config_file):
    """Creates a valid config file for local, unittest-based execution, returning
    the path to the config.
    """
    with open(config_file, mode="w") as handle:
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


def test_non_existent_session_file_returns_EX_NOINPUT(local_unittest_config):
    assert cosmic_ray.cli.main(["exec", str(local_unittest_config), "foo.session"]) == ExitCode.NO_INPUT


def test_non_existent_config_file_returns_EX_NOINPUT(session, local_unittest_config):
    cosmic_ray.cli.main(["init", local_unittest_config, str(session)])
    assert cosmic_ray.cli.main(["exec", "no-such-file", str(session)]) == ExitCode.CONFIG



def test_init_with_existing_results_no_force(session, local_unittest_config):
    """Test that init exits without reinitializing when results exist and force=False"""
    #lobotomize
    # Sample WorkItem creation
    mutation_spec = MutationSpec(
        module_path=Path("src/operators/util.py"),
        operator_name="extend_name",
        occurrence=1,
        start_pos=(10, 0),
        end_pos=(10, 20),
        operator_args={"comment": "Delete print statement"}
    )

    work_items = [
        WorkItem(
            job_id="test_job_123",
            mutations=(mutation_spec,)
        )
    ]
    
    with use_db(session,WorkDB.Mode.create) as db:
        db.add_work_items(work_items)
        execute(db,config=ConfigDict)

    
    with use_db(session,WorkDB.Mode.open) as db:
        initial_count = db.num_results

    # Verify initial database state has our test work item
    result = cosmic_ray.cli.main(["init", local_unittest_config, str(session)])
    with use_db(session,WorkDB.Mode.open) as db:
        final_count = db.num_results

    assert final_count == initial_count  # Confirm work items are unchanged
    assert result == ExitCode.OK 










def test_init_with_existing_results_force(session, local_unittest_config):
    """Test that reinitialization occurs when force=True"""
    mutation_spec = MutationSpec(
        module_path=Path("src/operators/test.py"),
        operator_name="delete_line",
        occurrence=1,
        start_pos=(10, 0),
        end_pos=(10, 20),
        operator_args={"comment": "Delete print statement"}
    )

    work_items = [
        WorkItem(
            job_id="test_job_123",
            mutations=(mutation_spec,)
        )
    ]
    
    with use_db(session,WorkDB.Mode.create) as db:
        db.add_work_items(work_items)
    

    instance=WorkDB()
    instance.set_result(WorkDB.Mode.open,config=ConfigDict)
    initial_count = db.num_results
    # Verify initial database state has our test work items
            
    result = cosmic_ray.cli.main(["init", local_unittest_config, str(session),"--force"])
    with use_db(session,WorkDB.Mode.open) as db:
        final_count = db.num_results
        execute(db,config=ConfigDict)

    assert initial_count!=0 and final_count == 0  

    assert result == ExitCode.OK

@pytest.mark.skip("need to sort this API out")
def test_unreadable_file_returns_EX_PERM(tmpdir, local_unittest_config):
    p = tmpdir.ensure("bogus.session.sqlite")
    p.chmod(stat.S_IRUSR)
    assert cosmic_ray.cli.main(["exec", local_unittest_config, str(p.realpath())]) == ExitCode.NO_PERM


def test_new_config_success_returns_EX_OK(monkeypatch, config_file):
    monkeypatch.setattr(cosmic_ray.commands, "new_config", lambda *args: "")
    errcode = cosmic_ray.cli.main(["new-config", config_file])
    assert errcode == ExitCode.OK


# NOTE: We have integration tests for the happy-path for many commands, so we don't cover them explicitly here.


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
