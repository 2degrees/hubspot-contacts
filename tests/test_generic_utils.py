from nose.tools import assert_not_in
from nose.tools import eq_

from hubspot.contacts.generic_utils import remove_unset_values_from_dict


class TestUnsetValueRemovalFromDict(object):

    _KEY = 'key'

    def test_set_value(self):
        input_dict = {self._KEY: 'value'}
        eq_(input_dict, remove_unset_values_from_dict(input_dict))

    def test_empty_dict(self):
        empty_dict = {}
        eq_(empty_dict, remove_unset_values_from_dict(empty_dict))

    def test_empty_string_value(self):
        input_dict = {self._KEY: ''}
        assert_not_in(self._KEY, remove_unset_values_from_dict(input_dict))

    def test_none_value(self):
        input_dict = {self._KEY: None}
        assert_not_in(self._KEY, remove_unset_values_from_dict(input_dict))

    def test_empty_list(self):
        input_dict = {self._KEY: []}
        assert_not_in(self._KEY, remove_unset_values_from_dict(input_dict))

    def test_false_value(self):
        input_dict = {self._KEY: False}
        eq_(input_dict, remove_unset_values_from_dict(input_dict))

    def test_zero_value(self):
        input_dict = {self._KEY: 0}
        eq_(input_dict, remove_unset_values_from_dict(input_dict))
