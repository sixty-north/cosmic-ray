import os
import stat

import cosmic_ray.cli


def test_invalid_command_line_returns_EX_USAGE():
    assert cosmic_ray.cli.main(['init', 'foo']) == os.EX_USAGE

def test_non_existent_file_returns_EX_NOINPUT():
    assert cosmic_ray.cli.main(['exec', 'foo.session']) == os.EX_NOINPUT

def test_unreadable_file_returns_EX_PERM(tmpdir):
    p = tmpdir.ensure('bogus.session.json')
    p.chmod(stat.S_IRUSR)
    assert cosmic_ray.cli.main(['exec', str(p.realpath())]) == os.EX_NOPERM
