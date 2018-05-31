from pytest import raises

from cosmic_ray.work_item import WorkItem


def test_work_item_constructed_with_no_arguments_contains_all_attributes_with_none_value():
    w = WorkItem()
    assert all(getattr(w, fieldname) is None for fieldname in WorkItem.FIELDS)


def test_work_item_constructed_with_no_arguments_contains_all_keys_with_none_value():
    w = WorkItem()
    assert all(w[fieldname] is None for fieldname in WorkItem.FIELDS)


def test_work_items_have_distinct_state():
    w = WorkItem()
    v = WorkItem()
    w.job_id = 42
    v.job_id = 39
    assert w.job_id != v.job_id


def test_setting_illegal_attributes_raises_attribute_error():
    w = WorkItem()
    with raises(AttributeError):
        w.foo = 19


def test_setting_illegal_key_raises_key_error():
    w = WorkItem()
    with raises(KeyError):
        w['foo'] = 38


def test_as_dict_on_default_constructed_work_item_contains_all_keys_with_none_value():
    w = WorkItem()
    d = w.as_dict()
    assert all(d[fieldname] is None for fieldname in WorkItem.FIELDS)


def test_as_dict_contains_same_values_as_modified_work_item():
    w = WorkItem()
    w.job_id = 1729
    d = w.as_dict()
    assert d['job_id'] == 1729
