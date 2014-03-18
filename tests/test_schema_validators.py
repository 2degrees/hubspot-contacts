##############################################################################
#
# Copyright (c) 2014, 2degrees Limited.
# All Rights Reserved.
#
# This file is part of hubspot-contacts
# <https://github.com/2degrees/hubspot-contacts>, which is subject to the
# provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from nose.tools import assert_raises
from nose.tools import eq_
from voluptuous import Invalid
from voluptuous import Schema

from hubspot.contacts._schemas._validators import AnyListItemValidates
from hubspot.contacts._schemas._validators import Constant
from hubspot.contacts._schemas._validators import DynamicDictionary
from hubspot.contacts._schemas._validators import GetDictValue


class TestGetttingDictValues(object):

    def setup(self):
        self.schema = Schema(GetDictValue('key'))

    def test_key_in_dictionary(self):
        eq_('abc', self.schema({'key': 'abc'}))

    def test_key_not_in_dictionary(self):
        with assert_raises(Invalid) as context_manager:
            self.schema({})

        exception = context_manager.exception
        eq_('expected key \'key\' in dictionary', str(exception))

    def test_not_a_dictionary(self):
        with assert_raises(Invalid) as context_manager:
            self.schema([1, 2])

        exception = context_manager.exception
        eq_('expected a dictionary', str(exception))


class TestDynamicDictionary(object):

    def setup(self):
        self.schema = Schema(DynamicDictionary(str, int))

    def test_valid_dictionary(self):
        dictionary = {'a': 1, 'b': 2}

        eq_(dictionary, self.schema(dictionary))

    def test_empty_dictionary(self):
        eq_({}, self.schema({}))

    def test_non_dictionary(self):
        """
        An 'Invalid' exception is raised when the value is not a dictionary

        """
        with assert_raises(Invalid):
            self.schema(('value', 'whatever'))

    def test_invalid_dictionary_key(self):
        """ An 'Invalid' exception is raised when any key is invalid """
        with assert_raises(Invalid):
            self.schema({1: 2})

    def test_invalid_dictionary_value(self):
        """ An 'Invalid' exception is raised when any value is invalid """
        with assert_raises(Invalid):
            self.schema({'value': [1, 2, 3]})


class TestAnyListItemValidates(object):

    def setup(self):
        self.schema = Schema(AnyListItemValidates(int))

    def test_contains(self):
        input_tuple = [1, 'string', []]

        eq_(input_tuple,  self.schema(input_tuple))

    def test_contains_multiple(self):
        input_tuple = [1, 2, 3]

        eq_(input_tuple,  self.schema(input_tuple))

    def test_doesnt_contain(self):
        input_tuple = ['string', []]

        with assert_raises(Invalid):
            self.schema(input_tuple)

    def test_is_not_iterable(self):
        with assert_raises(Invalid):
            self.schema(1)


class TestConstantValue(object):

    def setup(self):
        self.schema = Schema(Constant(1))

    def test_matching_value(self):
        eq_(1, self.schema(1))

    def test_non_matching_value(self):
        with assert_raises(Invalid):
            self.schema(2)
