import importlib

import pytest

from cosmic_ray.work_db import use_db
from cosmic_ray.work_item import WorkerOutcome

init_command = importlib.import_module("cosmic_ray.commands.init")


class PipeOperator:
    def mutation_positions(self, node):
        if getattr(node, "value", None) == "|":
            yield (node.start_pos, node.end_pos)


def test_default_annotation_filter_skips_annassign_and_preserves_occurrence(monkeypatch, tmpdir_path, session):
    monkeypatch.setattr(init_command, "_operators", lambda _cfgs: (("test/PipeOperator", {}, PipeOperator()),))

    module_path = tmpdir_path / "mod.py"
    module_path.write_text("x: int | str = 0\ny = 1 | 2\n")

    with use_db(session) as work_db:
        init_command.init([module_path], work_db, {})

        assert work_db.num_work_items == 2
        assert work_db.num_results == 1

        pending = work_db.pending_work_items
        assert len(pending) == 1
        assert pending[0].mutations[0].occurrence == 1

        completed = work_db.completed_work_items
        assert len(completed) == 1
        work_item, result = completed[0]
        assert work_item.mutations[0].occurrence == 0
        assert result.worker_outcome == WorkerOutcome.SKIPPED


def test_annotation_filter_allow_annassign_disables_skipping(monkeypatch, tmpdir_path, session):
    monkeypatch.setattr(init_command, "_operators", lambda _cfgs: (("test/PipeOperator", {}, PipeOperator()),))

    module_path = tmpdir_path / "mod.py"
    module_path.write_text("x: int | str = 0\ny = 1 | 2\n")

    with use_db(session) as work_db:
        init_command.init([module_path], work_db, {}, {"allow-contexts": ["annassign"]})

        assert work_db.num_work_items == 2
        assert work_db.num_results == 0
        pending_occurrences = sorted(item.mutations[0].occurrence for item in work_db.pending_work_items)
        assert pending_occurrences == [0, 1]


def test_default_annotation_filter_skips_param_and_return_annotations(monkeypatch, tmpdir_path, session):
    monkeypatch.setattr(init_command, "_operators", lambda _cfgs: (("test/PipeOperator", {}, PipeOperator()),))

    module_path = tmpdir_path / "mod.py"
    module_path.write_text("def f(x: int | str) -> int | str:\n    return 1 | 2\n")

    with use_db(session) as work_db:
        init_command.init([module_path], work_db, {})

        assert work_db.num_work_items == 3
        assert work_db.num_results == 2
        pending_occurrences = sorted(item.mutations[0].occurrence for item in work_db.pending_work_items)
        assert pending_occurrences == [2]


def test_annotation_filter_rejects_unknown_context(monkeypatch, tmpdir_path, session):
    monkeypatch.setattr(init_command, "_operators", lambda _cfgs: (("test/PipeOperator", {}, PipeOperator()),))

    module_path = tmpdir_path / "mod.py"
    module_path.write_text("x: int | str = 0\ny = 1 | 2\n")

    with use_db(session) as work_db:
        with pytest.raises(ValueError, match="Unknown annotation contexts"):
            init_command.init([module_path], work_db, {}, {"allow-contexts": ["unknown"]})
