import tokenize
from contextlib import contextmanager
from pathlib import Path


def read_python_source(module_filepath):
    """Load the code in a Python source file.

    Use this whenever reading source code from a Python source file!
    This takes care of handling the encoding of the file.

    Args:
        module_path: The path to the Python source file.

    Returns: A string contining the decoded source code from the file.
    """
    with tokenize.open(module_filepath) as handle:
        source = handle.read()
    return source


@contextmanager
def restore_contents(filepath: Path):
    """Restore the original contents of a file after a context-manager.

    Args:
        filepath (Path): Path to the file.

    Yields:
        bytes: The original contents of the file.
    """
    contents = filepath.read_bytes()
    try:
        yield contents
    finally:
        filepath.write_bytes(contents)
