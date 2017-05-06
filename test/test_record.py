from cosmic_ray.work_record import make_record
from hypothesis import given, assume
import hypothesis.strategies as ST
import pytest
import string

attributes = ST.text(alphabet=string.ascii_letters, min_size=1, max_size=10)


@given(attributes)
def test_empty_constructor_has_no_attributes(attr):
    r = make_record('Rec')()
    with pytest.raises(AttributeError):
        getattr(r, attr)


def test_empty_constructor_has_no_keys():
    r = make_record('Rec')()
    assert len(r) == 0


@given(ST.sets(attributes))
def test_default_attr_value_is_none(attrs):
    r = make_record('Rec', attrs)()
    for attr in attrs:
        assert getattr(r, attr) is None
    assert len(r) == len(attrs)


@given(attributes, ST.text())
def test_can_assign_to_field_attributes(attr, value):
    r = make_record('Rec', [attr])()
    setattr(r, attr, value)
    assert getattr(r, attr) == value


@given(attributes, attributes)
def test_cannot_assign_to_non_field_attributes(attr, nonattr):
    assume(attr != nonattr)
    r = make_record('Rec', [attr])()
    with pytest.raises(AttributeError):
        r.bar = 'llama'


@given(attributes)
def test_can_index_fields(attr):
    r = make_record('Rec', [attr])()
    r[attr] = 42
    assert r[attr] == 42


@given(attributes, attributes)
def test_cannot_index_non_fields(attr, nonattr):
    assume(attr != nonattr)
    r = make_record('Rec', [attr])()
    with pytest.raises(KeyError):
        r[nonattr] = 42
    with pytest.raises(KeyError):
        r[nonattr]


@given(attributes)
def test_can_update_fields(attr):
    r = make_record('Rec', [attr])()
    r.update({attr: 42})
    assert r[attr] == 42


@given(attributes, attributes)
def test_cannot_update_non_fields(attr, nonattr):
    assume(attr != nonattr)
    r = make_record('Rec', [attr])()
    with pytest.raises(KeyError):
        r.update({nonattr: 42})


@given(attributes)
def test_cannot_delete_fields(attr):
    r = make_record('Rec', [attr])()
    with pytest.raises(KeyError):
        del r[attr]


@given(ST.sets(attributes))
def test_can_construct_from_dict(attrs):
    make_record('Rec', attrs)({a: 42 for a in attrs})


@given(attributes, attributes)
def test_cannot_construct_from_dict_with_non_fields(attr, nonattr):
    assume(attr != nonattr)
    R = make_record('Rec', [attr])
    with pytest.raises(KeyError):
        R({nonattr: 3})
