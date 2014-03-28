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

from functools import partial

from nose.tools import assert_in
from nose.tools import assert_raises
from nose.tools import eq_
from voluptuous import MultipleInvalid

from hubspot.contacts.exc import HubspotClientError
from hubspot.contacts.generic_utils import remove_unset_values_from_dict
from hubspot.contacts.properties import BooleanProperty
from hubspot.contacts.properties import DatetimeProperty
from hubspot.contacts.properties import EnumerationProperty
from hubspot.contacts.properties import NumberProperty
from hubspot.contacts.properties import Property
from hubspot.contacts.properties import StringProperty
from hubspot.contacts.properties import create_property
from hubspot.contacts.properties import delete_property
from hubspot.contacts.properties import get_all_properties
from hubspot.contacts.properties import get_property_type_name
from hubspot.contacts.properties import get_raw_property_options
from hubspot.test_utils import MockPortalConnection
from hubspot.test_utils import RemoteMethod

from tests.utils import BaseMethodTestCase
from tests.utils import ConstantResponseDataMaker
from tests.utils.generic import get_uuid4_str


_STUB_PROPERTY = Property(
    'is_polite',
    'Is contact polite?',
    'Whether the contact is polite',
    'social_interaction',
    'booleancheckbox',
    )


class TestGettingAllProperties(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/properties', 'GET')

    def test_no_properties(self):
        response_data_maker_by_remote_method = \
            {self._REMOTE_METHOD: ConstantResponseDataMaker([])}
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        retrieved_properties = get_all_properties(connection)
        self._assert_expected_remote_method_used(connection)

        eq_(0, len(retrieved_properties))

    def test_multiple_properties(self):
        properties = [
            BooleanProperty.init_from_generalization(_STUB_PROPERTY),
            DatetimeProperty.init_from_generalization(_STUB_PROPERTY),
            ]
        response_data_maker = partial(
            _replicate_get_all_properties_response_data,
            properties,
            )
        response_data_maker_by_remote_method = \
            {self._REMOTE_METHOD: response_data_maker}
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        retrieved_properties = get_all_properties(connection)

        self._assert_expected_remote_method_used(connection)

        eq_(properties, retrieved_properties)

    #{ Property specializations

    def test_boolean(self):
        boolean_property = \
            BooleanProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(boolean_property)

    def test_datetime(self):
        datetime_property = \
            DatetimeProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(datetime_property)

    def test_enumeration(self):
        enumeration_property = EnumerationProperty.init_from_generalization(
            _STUB_PROPERTY,
            options={'label1': 'value1', 'label2': 'value2'},
            )
        self._check_property_retrieval(enumeration_property)

    def test_number(self):
        number_property = \
            NumberProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(number_property)

    def test_string(self):
        string_property = \
            StringProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(string_property)

    def _check_property_retrieval(self, property_):
        response_data_maker = \
            partial(_replicate_get_all_properties_response_data, [property_])
        response_data_maker_by_remote_method = \
            {self._REMOTE_METHOD: response_data_maker}
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        retrieved_properties = get_all_properties(connection)

        eq_(1, len(retrieved_properties))
        eq_(property_, retrieved_properties[0])

    def test_unsupported_type(self):
        response_data_maker_by_remote_method = {
            self._REMOTE_METHOD:
                _replicate_get_all_properties_invalid_response_data,
            }
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        assert_raises(
            MultipleInvalid,
            get_all_properties,
            connection,
            )

    #}


class TestCreatingProperty(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/properties/' + _STUB_PROPERTY.name, 'PUT')

    def test_all_fields_set(self):
        property_ = NumberProperty.init_from_generalization(_STUB_PROPERTY)

        self._check_create_property(property_, property_)

    def test_enum_options(self):
        property_ = EnumerationProperty.init_from_generalization(
            _STUB_PROPERTY,
            options={'Yes': 'yes', 'No': 'no', 'Unknown': 'unknown'},
            )

        self._check_create_property(property_, property_)

    def test_some_fields_unset(self):
        property_ = StringProperty.init_from_generalization(_STUB_PROPERTY)
        property_.description = None

        expected_created_property = property_.copy()
        expected_created_property.description = ''

        self._check_create_property(property_, expected_created_property)

    def test_already_exists(self):
        self._assert_error_response(
            _replicate_create_property_duplicate_error_response,
            'name',
            )

    def test_non_existing_group(self):
        self._assert_error_response(
            _replicate_create_property_invalid_group_error_response,
            'group_name',
            )

    @classmethod
    def _check_create_property(cls, property_, expected_property):
        property_data = _get_data_from_property(property_)
        response_data_maker_by_remote_method = \
            {cls._REMOTE_METHOD: ConstantResponseDataMaker(property_data)}
        connection = MockPortalConnection(response_data_maker_by_remote_method)
        created_property = create_property(property_, connection)

        eq_(1, len(connection.remote_method_invocations))
        remote_method_invocation = connection.remote_method_invocations[0]

        expected_remote_method_invocation = \
            remove_unset_values_from_dict(property_data)
        eq_(
            expected_remote_method_invocation,
            remote_method_invocation.body_deserialization,
            )

        eq_(expected_property, created_property)

    @classmethod
    def _assert_error_response(
        cls,
        error_generator,
        attribute_name_in_error_msg,
        ):
        property_ = StringProperty.init_from_generalization(_STUB_PROPERTY)
        response_data_maker_by_remote_method = \
            {cls._REMOTE_METHOD: error_generator}
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        with assert_raises(HubspotClientError) as context_manager:
            create_property(property_, connection)

        exception = context_manager.exception
        attribute_in_error_msg = getattr(property_, attribute_name_in_error_msg)
        assert_in(attribute_in_error_msg, str(exception))


class TestPropertyDeletion(BaseMethodTestCase):

    _PROPERTY_NAME = 'test'

    _REMOTE_METHOD = RemoteMethod('/properties/' + _PROPERTY_NAME, 'DELETE')

    def test_existing_mutable_property(self):
        connection = MockPortalConnection()
        delete_property(self._PROPERTY_NAME, connection)

        self._assert_expected_remote_method_used(connection)

        eq_(1, len(connection.remote_method_invocations))


def _replicate_create_property_duplicate_error_response(
    query_string_args,
    body_deserialization,
    ):
    property_name = body_deserialization['name']
    raise HubspotClientError(
        "The Property named '{}' already exists.".format(property_name),
        get_uuid4_str(),
        )


def _replicate_create_property_invalid_group_error_response(
    query_string_args,
    body_deserialization,
    ):
    property_group_name = body_deserialization['groupName']
    raise HubspotClientError(
        "group '{}' does not exist.".format(property_group_name),
        get_uuid4_str(),
        )


def _replicate_get_all_properties_response_data(
    properties,
    query_string_args,
    body_deserialization,
    ):
    properties_data = [_get_data_from_property(p) for p in properties]
    return properties_data


def _get_data_from_property(property_):
    property_type = get_property_type_name(property_)
    property_options = get_raw_property_options(property_)
    property_data = {
        'name': property_.name,
        'label': _convert_none_to_empty_string(property_.label),
        'description': _convert_none_to_empty_string(property_.description),
        'groupName': property_.group_name,
        'fieldType': _convert_none_to_empty_string(property_.field_widget),
        'type': property_type,
        'options': property_options,
        }
    return property_data


def _replicate_get_all_properties_invalid_response_data(
    remote_method,
    body_deserialization,
    ):
    properties = [{
        'name': 'name',
        'label': 'label',
        'description': 'description',
        'groupName': 'group_name',
        'fieldType': 'field_widget',
        'type': 'invalid_type',
        'options': [],
        }]
    return properties


def _convert_none_to_empty_string(value):
    return '' if value is None else value
