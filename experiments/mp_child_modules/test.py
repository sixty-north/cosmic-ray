import multiprocessing
import os
import sys


def foo():
    # It seems that 'uuid' is in sys.modules only because the parent
    # process imported it. I suppose this makes some sense from a use
    # point of view. Does the child unilaterally import everything
    # from the parent parent's sys.modules?
    print(os.getpid())
    assert 'uuid' in sys.modules


def parent_only():
    import uuid
    print(os.getpid())
    p = multiprocessing.Process(target=foo)
    p.start()
    p.join()


if __name__ == '__main__':
    parent_only()
