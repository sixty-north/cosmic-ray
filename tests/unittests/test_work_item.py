"Tests covering types in work_item."

from pathlib import Path

from cosmic_ray.work_item import MutationSpec


def test_mutation_spec_accepts_str_module_path():
    mutation = MutationSpec("foo/bar.py", "operator", 0, (0, 0), (0, 1))

    assert mutation.module_path == Path("foo/bar.py")
