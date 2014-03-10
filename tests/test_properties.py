from nose.tools import eq_

from hubspot.contacts.properties import Property
from hubspot.contacts.properties import get_all_properties

from tests.utils import BaseMethodTestCase
from tests.utils import RemoteMethod
from tests.utils.connection import MockPortalConnection


class TestGettingAllProperties(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/properties', 'GET')

    def test(self):
        connection = \
            MockPortalConnection(_replicate_get_all_properties_response_data)

        retrieved_properties = get_all_properties(connection)

        expected_properties = [Property('lastmodifieddate', 'datetime', [])]
        eq_(expected_properties, retrieved_properties)

        self._assert_expected_remote_method_used(connection)


def _replicate_get_all_properties_response_data(request_data):
    return [{'name': u'lastmodifieddate', 'type': 'datetime', 'options': []}]
