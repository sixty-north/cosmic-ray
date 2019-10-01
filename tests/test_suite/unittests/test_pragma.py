from cosmic_ray.pragma import get_pragma_list


def test_pragma():
    r = get_pragma_list("# comment")
    assert r is None
    r = get_pragma_list("# comment pragma:")
    assert r == {}
    r = get_pragma_list("# comment pragma: x y  z")
    assert r == {'x y': None, 'z': None}
    r = get_pragma_list("# comment pragma: x:")
    assert r == {'x': []}
    r = get_pragma_list("# comment pragma: x:  y")
    assert r == {'x': [], 'y': None}
    r = get_pragma_list("# comment pragma: x y  z: d, e")
    assert r == {'x y': None, 'z': ['d', 'e']}
    r = get_pragma_list("# comment pragma: x: a, b, c  y z: d, e")
    assert r == {'x': ['a', 'b', 'c'], 'y z': ['d', 'e']}
    r = get_pragma_list("comment pragma: x: a, b, c y  z: d, e")
    assert r == {'x': ['a', 'b', 'c y'], 'z': ['d', 'e']}
