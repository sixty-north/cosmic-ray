import contextlib
import os.path
import tempfile

import with_fixture

import cosmic_ray.modules


@contextlib.contextmanager
def excursion(directory):
    old_dir = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(old_dir)


def make_file(path):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'wt'):
        pass


class FindModulesTest(with_fixture.TestCase):
    def withFixture(self):
        # NOTE: We use dir= here because on some operating systems (OS
        # X *ahem*) the temp directory can be created in /var which is
        # some sort of magic alias for /private/var. This can make the
        # test results appear incorrect when in fact they're fine.
        with tempfile.TemporaryDirectory(
                dir=os.path.dirname(__file__)) as self.root:
            with excursion(self.root):
                yield

    def test_small_directory_tree(self):
        paths = [['a', '__init__.py'],
                 ['a', 'b.py'],
                 ['a', 'c', '__init__.py'],
                 ['a', 'c', 'd.py']]
        paths = [os.path.abspath(os.path.join(self.root, *path))
                 for path in paths]
        [make_file(p) for p in paths]

        results = cosmic_ray.modules.find_modules('a')
        self.assertListEqual(
            sorted(paths),
            sorted(map(lambda m: m.__file__, results)))
