from simple_math import square, cube, mult_by_2, is_positive


def test_square():
    assert square(3) == 9


def test_cube():
    assert cube(2) == 8


def test_mult_by_2():
    assert mult_by_2(2) == 4


def test_is_positive_for_positive_numbers():
    assert is_positive(1)
    assert is_positive(2)
    assert is_positive(3)


def test_is_positive_for_non_positive_numbers():
    assert not is_positive(0)
    assert not is_positive(-1)
    assert not is_positive(-2)
