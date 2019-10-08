import parso

from cosmic_ray.operators.util import dump_node


def test_dump_node():
    s = open(__file__).read()
    node = parso.parse(s)
    dump_node(node)
