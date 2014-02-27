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

from nose.tools import assert_false
from nose.tools import assert_in
from nose.tools import eq_

from hubspot.contacts import Contact
from hubspot.contacts import get_all_contacts

from tests.utils.connection import MockPortalConnection
from tests.utils.contact import make_contact
from tests.utils.contact import make_contacts
from tests.utils.method_response_formatters.all_contacts_retrieval import \
    format_data_from_all_contacts_retrieval


_DEFAULT_PAGE_SIZE = 20


class TestGettingAllContacts(object):

    def test_no_contacts(self):
        connection = MockPortalGetAllContactsConnection([])

        self._assert_retrieved_contacts_match([], connection)

        self._assert_expected_path_infos_requested(connection)

        eq_(1, len(connection.requests_data))
        request_data = connection.requests_data[0]
        assert_false(request_data.query_string_args)

    def test_not_exceeding_default_pagination_size(self):
        contacts_count = _DEFAULT_PAGE_SIZE - 1
        expected_contacts = make_contacts(contacts_count)
        connection = MockPortalGetAllContactsConnection(expected_contacts)

        self._assert_retrieved_contacts_match(expected_contacts, connection)

        self._assert_expected_path_infos_requested(connection)

        eq_(1, len(connection.requests_data))
        request_data = connection.requests_data[0]
        assert_false(request_data.query_string_args)

    def test_exceeding_default_pagination_size(self):
        contacts_count = _DEFAULT_PAGE_SIZE + 1
        expected_contacts = make_contacts(contacts_count)
        connection = MockPortalGetAllContactsConnection(expected_contacts)

        self._assert_retrieved_contacts_match(expected_contacts, connection)

        self._assert_expected_path_infos_requested(connection)

        eq_(2, len(connection.requests_data))

        request_data1 = connection.requests_data[0]
        assert_false(request_data1.query_string_args)

        request_data2 = connection.requests_data[1]
        eq_(1, len(request_data2.query_string_args))
        assert_in('vidOffset', request_data2.query_string_args)

    def test_not_exceeding_custom_pagination_size(self):
        contacts_count = _DEFAULT_PAGE_SIZE
        expected_contacts = make_contacts(contacts_count)
        connection = MockPortalGetAllContactsConnection(expected_contacts)

        page_size = contacts_count + 1
        self._assert_retrieved_contacts_match(
            expected_contacts,
            connection,
            page_size,
            )

        self._assert_expected_path_infos_requested(connection)

        eq_(1, len(connection.requests_data))
        request_data = connection.requests_data[0]
        eq_(1, len(request_data.query_string_args))
        assert_in('count', request_data.query_string_args)
        eq_(page_size, request_data.query_string_args['count'])

    def test_exceeding_custom_pagination_size(self):
        contacts_count = _DEFAULT_PAGE_SIZE
        expected_contacts = make_contacts(contacts_count)
        connection = MockPortalGetAllContactsConnection(expected_contacts)

        page_size = contacts_count - 1
        self._assert_retrieved_contacts_match(
            expected_contacts,
            connection,
            page_size,
            )

        self._assert_expected_path_infos_requested(connection)

        eq_(2, len(connection.requests_data))

        request_data1 = connection.requests_data[0]
        eq_(1, len(request_data1.query_string_args))
        assert_in('count', request_data1.query_string_args)
        eq_(page_size, request_data1.query_string_args['count'])

        request_data2 = connection.requests_data[1]
        eq_(2, len(request_data2.query_string_args))
        assert_in('count', request_data2.query_string_args)
        eq_(page_size, request_data2.query_string_args['count'])
        assert_in('vidOffset', request_data2.query_string_args)

    def test_getting_existing_properties(self):
        expected_contacts = [
            make_contact(1, p1='foo'),
            make_contact(2, p1='baz', p2='bar'),
            ]
        connection = MockPortalGetAllContactsConnection(expected_contacts)

        expected_contacts_with_expected_properties = []
        for original_contact in expected_contacts:
            expected_contact_with_expected_properties = Contact(
                original_contact.vid,
                original_contact.email_address,
                {'p1': original_contact.properties['p1']},
                )
            expected_contacts_with_expected_properties.append(
                expected_contact_with_expected_properties,
                )

        properties = ('p1',)
        self._assert_retrieved_contacts_match(
            expected_contacts_with_expected_properties,
            connection,
            properties=properties,
            )

        self._assert_expected_path_infos_requested(connection)

        eq_(1, len(connection.requests_data))
        request_data = connection.requests_data[0]
        eq_(1, len(request_data.query_string_args))
        assert_in('property', request_data.query_string_args)
        eq_(properties, request_data.query_string_args['property'])

    def test_getting_non_existing_properties(self):
        """Requesting non-existing properties fails silently in HubSpot"""
        expected_contacts = make_contacts(_DEFAULT_PAGE_SIZE)
        connection = MockPortalGetAllContactsConnection(expected_contacts)

        self._assert_retrieved_contacts_match(expected_contacts, connection)

        self._assert_expected_path_infos_requested(connection)

        eq_(1, len(connection.requests_data))

    def _assert_retrieved_contacts_match(
        self,
        expected_contacts,
        connection,
        *args,
        **kwargs
        ):
        retrieved_contacts = get_all_contacts(connection, *args, **kwargs)
        eq_(list(expected_contacts), list(retrieved_contacts))

    def _assert_expected_path_infos_requested(self, connection):
        connection.assert_requested_path_infos_equal('/lists/all/contacts/all')


class MockPortalGetAllContactsConnection(MockPortalConnection):

    def __init__(self, contacts):
        super(MockPortalGetAllContactsConnection, self).__init__()

        self._contacts = contacts

    def _get_stub_data(self, request_data):
        query_string_args = request_data.query_string_args
        page_size = query_string_args.get('count', _DEFAULT_PAGE_SIZE)
        last_contact_vid = query_string_args.get('vidOffset')
        properties = query_string_args.get('property', [])

        contacts_in_page = \
            _get_contacts_in_page(self._contacts, last_contact_vid, page_size)
        contacts_in_page = \
            _get_contacts_with_properties_filtered(contacts_in_page, properties)
        contacts_in_page_data = format_data_from_all_contacts_retrieval(
            contacts_in_page,
            self._contacts,
            page_size,
            )
        return contacts_in_page_data


def _get_contacts_in_page(contacts, last_contact_vid, page_size):
    start_index = 0
    if last_contact_vid:
        for contact_index, contact in enumerate(contacts):
            if contact.vid == last_contact_vid:
                start_index = contact_index + 1
                break
    end_index = start_index + page_size
    contacts_in_page = contacts[start_index:end_index]
    return contacts_in_page


def _get_contacts_with_properties_filtered(contacts, properties):
    if not properties:
        return contacts

    contacts_with_properties_filtered = []
    for contact in contacts:
        contact_with_properties_filtered = contact.copy()
        contact_with_properties_filtered.properties = \
            {k: v for k, v in contact.properties.items() if k in properties}

        contacts_with_properties_filtered. \
            append(contact_with_properties_filtered)

    return contacts_with_properties_filtered
