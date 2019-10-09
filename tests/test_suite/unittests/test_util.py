import parso

from cosmic_ray.ast import dump_node


def test_dump_node():
    s = open(__file__).read()
    node = parso.parse(s)
    d = dump_node(node)
    assert isinstance(d, str)
