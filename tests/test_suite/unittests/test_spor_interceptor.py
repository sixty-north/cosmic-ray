import pytest

from cosmic_ray.work_item import WorkItem
from cosmic_ray.interceptors.spor import _item_in_context, _line_and_col_to_offset
from spor.anchor import Context


@pytest.fixture
def lines():
    return ['123\n', '456\n', '789']


class Test_line_and_col_to_offset:
    def test_simple(self, lines):
        offset = _line_and_col_to_offset(lines, 2, 1)
        assert offset == 5

    def test_non_existent_col(self, lines):
        assert _line_and_col_to_offset(lines, 3, 5) == 13

    def test_raises_value_error_for_bad_line(self, lines):
        with pytest.raises(ValueError):
            _line_and_col_to_offset(lines, 4, 1)

    def test_raises_value_error_for_one_past_end(self, lines):
        assert _line_and_col_to_offset(lines, 3, 3) == 11

    def test_first_char(self, lines):
        assert _line_and_col_to_offset(lines, 1, 0) == 0

    def test_last_char(self, lines):
        assert _line_and_col_to_offset(lines, 3, 2) == 10


class Test_item_in_context:
    def test_positive(self, lines):
        item = WorkItem(
            module_path='foo.py',
            operator_name='operator',
            occurrence=0,
            start_pos=(1, 1),
            end_pos=(2, 3),
            job_id='jobid')

        context = Context(
            offset=0, topic=' ' * 11, before='', after='', width=0)

        assert _item_in_context(lines, item, context)

    def test_positive_for_perfect_match(self, lines):
        item = WorkItem(
            module_path='foo.py',
            operator_name='operator',
            occurrence=0,
            start_pos=(1, 0),
            end_pos=(3, 2),
            job_id='jobid')

        context = Context(
            offset=0, topic=' ' * 11, before='', after='', width=0)

        assert _item_in_context(lines, item, context)

    def test_negative_fully_outside(self, lines):
        item = WorkItem(
            module_path='foo.py',
            operator_name='operator',
            occurrence=0,
            start_pos=(1, 0),
            end_pos=(1, 2),
            job_id='jobid')

        context = Context(offset=5, topic='', before='', after='', width=3)

        assert not _item_in_context(lines, item, context)

    def test_negative_overlap_front(self, lines):
        item = WorkItem(
            module_path='foo.py',
            operator_name='operator',
            occurrence=0,
            start_pos=(1, 0),
            end_pos=(2, 0),
            job_id='jobid')

        context = Context(offset=1, topic='', before='', after='', width=2)

        assert not _item_in_context(lines, item, context)

    def test_negative_overlap_back(self, lines):
        item = WorkItem(
            module_path='foo.py',
            operator_name='operator',
            occurrence=0,
            start_pos=(2, 0),
            end_pos=(3, 3),
            job_id='jobid')

        context = Context(offset=5, topic='', before='', after='', width=6)

        assert not _item_in_context(lines, item, context)
