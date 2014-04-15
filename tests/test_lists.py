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

from inspect import isgenerator

from hubspot.connection.testing import ConstantResponseDataMaker
from hubspot.connection.testing import MockPortalConnection
from hubspot.connection.testing import RemoteMethod
from nose.tools import eq_
from nose.tools import ok_

from hubspot.contacts.lists import ContactList
from hubspot.contacts.lists import get_all_contact_lists

from tests.utils import BaseMethodTestCase


_MOCK_CONTACT_LIST_DATA = {
    'listId': 1,
    'name': 'atestlist',
    'dynamic': False,
    }

_MOCK_CONTACT_LIST = ContactList(
    _MOCK_CONTACT_LIST_DATA['listId'],
    _MOCK_CONTACT_LIST_DATA['name'],
    _MOCK_CONTACT_LIST_DATA['dynamic'],
    )


class TestContactListsRetrieval(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/contacts/v1/lists', 'GET')

    def test_no_contact_lists(self):
        connection = self._make_connection_with_contact_lists([])

        contact_lists = get_all_contact_lists(connection)

        self._assert_expected_remote_method_used(connection)

        eq_([], list(contact_lists))
        ok_(len(connection.remote_method_invocations))

    def test_getting_existing_contact_lists(self):
        connection = self._make_connection_with_contact_lists(
            [_MOCK_CONTACT_LIST_DATA],
            )

        contact_lists = get_all_contact_lists(connection)
        contact_lists = list(contact_lists)

        self._assert_expected_remote_method_used(connection)

        expected_contact_lists = [_MOCK_CONTACT_LIST]
        eq_(expected_contact_lists, contact_lists)

        ok_(len(connection.remote_method_invocations))

    def test_is_generator(self):
        connection = self._make_connection_with_contact_lists([])

        contact_lists = get_all_contact_lists(connection)
        ok_(isgenerator(contact_lists))

    def _make_connection_with_contact_lists(self, contact_lists):
        response_data = {'has-more': False, 'offset': 9, 'lists': contact_lists}
        connection = MockPortalConnection({
            self._REMOTE_METHOD: ConstantResponseDataMaker(response_data),
            })
        return connection
