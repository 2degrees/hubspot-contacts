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
"""
Test utilities.

These are not unit tested because they're considered part of the test suite,
so doing so would mean testing the tests.

"""

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from datetime import datetime
from json import dumps as json_serialize
from math import ceil

from hubspot.connection.testing import APICall
from hubspot.connection.testing import SuccessfulAPICall
from hubspot.connection.testing import UnsuccessfulAPICall

from hubspot.contacts._constants import BATCH_RETRIEVAL_SIZE_LIMIT
from hubspot.contacts._constants import BATCH_SAVING_SIZE_LIMIT
from hubspot.contacts._constants import CONTACTS_API_SCRIPT_NAME
from hubspot.contacts.generic_utils import \
    convert_date_to_timestamp_in_milliseconds
from hubspot.contacts.generic_utils import \
    convert_timestamp_in_milliseconds_to_datetime
from hubspot.contacts.generic_utils import get_uuid4_str
from hubspot.contacts.generic_utils import paginate
from hubspot.contacts.request_data_formatters.contacts import \
    format_contacts_data_for_saving
from hubspot.contacts.request_data_formatters.properties import \
    format_data_for_property
from hubspot.contacts.request_data_formatters.property_groups import \
    format_data_for_property_group as format_request_data_for_property_group


class _PaginatedObjectsRetriever(object):

    __metaclass__ = ABCMeta

    _API_CALL_PATH_INFO = abstractproperty()

    _OBJECT_DATA_KEY = abstractproperty()

    def __init__(self, objects):
        super(_PaginatedObjectsRetriever, self).__init__()
        self._objects_by_page = paginate(objects, BATCH_RETRIEVAL_SIZE_LIMIT)

    def __call__(self):
        api_calls = []

        if self._objects_by_page:
            first_page_objects = self._objects_by_page[0]
        else:
            first_page_objects = []

        first_page_api_call = self._get_api_call_for_page(first_page_objects)
        api_calls.append(first_page_api_call)

        subsequent_pages_objects = self._objects_by_page[1:]
        for page_objects in subsequent_pages_objects:
            api_call = self._get_api_call_for_page(page_objects)
            api_calls.append(api_call)

        return api_calls

    def _get_api_call_for_page(self, page_objects):
        query_string_args = self._get_query_string_args(page_objects)
        response_body_deserialization = \
            self._get_response_body_deserialization(page_objects)
        api_call = SuccessfulAPICall(
            CONTACTS_API_SCRIPT_NAME + self._API_CALL_PATH_INFO,
            'GET',
            query_string_args,
            response_body_deserialization=response_body_deserialization,
            )
        return api_call

    def _get_query_string_args(self, page_objects):
        query_string_args = {'count': BATCH_RETRIEVAL_SIZE_LIMIT}

        page_number = self._get_current_objects_page_number(page_objects)
        if 1 < page_number:
            query_string_args_for_page = \
                self._get_query_string_args_for_page(page_number)
            query_string_args.update(query_string_args_for_page)

        return query_string_args

    @abstractmethod
    def _get_query_string_args_for_page(self, page_number):
        pass  # pragma: no cover

    def _get_response_body_deserialization(self, page_objects):
        page_number = self._get_current_objects_page_number(page_objects)
        pages_count = len(self._objects_by_page)
        page_has_successors = page_number < pages_count

        page_objects_data = self._get_objects_data(page_objects)
        response_body_deserialization = {
            'has-more': page_has_successors,
            self._OBJECT_DATA_KEY: page_objects_data,
            }

        response_body_deserialization.update(
            self._get_response_body_deserialization_for_page(page_objects)
            )

        return response_body_deserialization

    @abstractmethod
    def _get_response_body_deserialization_for_page(self, page_objects):
        pass  # pragma: no cover

    def _get_current_objects_page_number(self, page_objects):
        if self._objects_by_page:
            page_number = self._objects_by_page.index(page_objects) + 1
        else:
            page_number = 1
        return page_number

    @abstractmethod
    def _get_objects_data(self, objects):
        pass  # pragma: no cover


class GetAllContacts(_PaginatedObjectsRetriever):

    _API_CALL_PATH_INFO = '/lists/all/contacts/all'

    _OBJECT_DATA_KEY = 'contacts'

    def __init__(self, contacts, available_properties, property_names=()):
        super(GetAllContacts, self).__init__(contacts)

        self._available_properties_simulator = \
            GetAllProperties(available_properties)
        self._property_names = property_names

    def __call__(self):
        api_calls = self._available_properties_simulator()
        api_calls.extend(super(GetAllContacts, self).__call__())
        return api_calls

    def _get_query_string_args(self, page_contacts):
        query_string_args = \
            super(GetAllContacts, self)._get_query_string_args(page_contacts)

        if self._property_names:
            query_string_args['property'] = self._property_names

        return query_string_args

    def _get_query_string_args_for_page(self, page_number):
        previous_page_contacts = self._objects_by_page[page_number - 2]
        previous_page_last_contact = previous_page_contacts[-1]
        query_string_args_for_page = \
            {'vidOffset': previous_page_last_contact.vid}
        return query_string_args_for_page

    def _get_response_body_deserialization_for_page(self, page_contacts):
        page_last_contact = page_contacts[-1] if page_contacts else None
        page_last_contact_vid = \
            page_last_contact.vid if page_last_contact else 0
        response_body_deserialization_for_page = {
            'vid-offset': page_last_contact_vid,
            }
        return response_body_deserialization_for_page

    def _get_objects_data(self, contacts):
        contacts_data = []
        for contact in contacts:
            contact_properties_data = \
                self._get_contact_properties_data(contact.properties)
            contact_profiles_data = self._get_contact_profiles_data(contact)
            contact_data = {
                'vid': contact.vid,
                'canonical-vid': contact.vid,
                'properties': contact_properties_data,
                'identity-profiles': contact_profiles_data,
                }
            contacts_data.append(contact_data)

        return contacts_data

    def _get_contact_properties_data(self, contact_properties):
        contact_properties_data = {}
        for property_name in self._property_names:
            if property_name not in contact_properties:
                continue
            property_value = \
                self._get_property_value(property_name, contact_properties)
            contact_properties_data[property_name] = {
                'value': property_value,
                'versions': [],
                }
        return contact_properties_data

    @staticmethod
    def _get_property_value(property_name, contact_properties):
        property_value = contact_properties[property_name]
        if isinstance(property_value, bool):
            property_value = json_serialize(property_value)
        elif isinstance(property_value, datetime):
            property_value = \
                convert_date_to_timestamp_in_milliseconds(property_value)

        property_value = unicode(property_value)
        return property_value

    @staticmethod
    def _get_contact_profiles_data(contact):
        contact_profile_data = {
            'vid': contact.vid,
            'identities': [
                {'type': 'LEAD_GUID', 'value': get_uuid4_str()},
                {'type': 'EMAIL', 'value': contact.email_address},
                ],
            }
        contact_profiles_data = [contact_profile_data]

        for vid in contact.related_contact_vids:
            contact_profiles_data.append({'vid': vid, 'identities': []})

        return contact_profiles_data


class UnsuccessfulGetAllContacts(GetAllContacts):

    def __init__(
        self,
        contacts,
        successful_api_call_count,
        exception,
        available_properties,
        property_names=(),
        ):

        minimum_contact_count = \
            BATCH_RETRIEVAL_SIZE_LIMIT * successful_api_call_count
        are_no_contacts = minimum_contact_count == 0
        assert are_no_contacts or minimum_contact_count < len(contacts), \
            'Need at least {} contacts to satisfy successful API calls'.format(
                minimum_contact_count,
                )

        super(UnsuccessfulGetAllContacts, self).__init__(
            contacts,
            available_properties,
            property_names,
            )
        self._expection = exception
        self._successful_api_call_count = successful_api_call_count

    def __call__(self):
        api_call_cutoff_index = self._successful_api_call_count + 1
        get_all_contacts_api_calls = \
            super(UnsuccessfulGetAllContacts, self).__call__()

        successful_api_calls = \
            get_all_contacts_api_calls[:api_call_cutoff_index]

        failing_api_call = get_all_contacts_api_calls[api_call_cutoff_index]
        unsuccessful_api_call = UnsuccessfulAPICall(
            failing_api_call.url_path,
            failing_api_call.http_method,
            failing_api_call.query_string_args,
            exception=self._expection,
            )

        api_calls = successful_api_calls + [unsuccessful_api_call]
        return api_calls


class GetAllContactsByLastUpdate(GetAllContacts):

    _API_CALL_PATH_INFO = '/lists/recently_updated/contacts/recent'

    MOST_RECENT_CONTACT_UPDATE_DATETIME = datetime.now()

    _MOST_RECENT_CONTACT_UPDATE_TIMESTAMP = \
        convert_date_to_timestamp_in_milliseconds(
            MOST_RECENT_CONTACT_UPDATE_DATETIME,
            )

    def __init__(
        self,
        contacts,
        available_properties,
        property_names=(),
        cutoff_datetime=None,
        ):

        filtered_contacts = self._exclude_contacts_pages_after_cutoff_datetime(
            contacts,
            cutoff_datetime,
            )

        super(GetAllContactsByLastUpdate, self).__init__(
            filtered_contacts,
            available_properties,
            property_names=property_names,
            )

        self._contacts = filtered_contacts

    @classmethod
    def _exclude_contacts_pages_after_cutoff_datetime(
        cls,
        contacts,
        cutoff_datetime,
        ):
        if not cutoff_datetime:
            filtered_contacts = contacts

        elif cutoff_datetime <= cls.MOST_RECENT_CONTACT_UPDATE_DATETIME:
            cutoff_timestamp = \
                convert_date_to_timestamp_in_milliseconds(cutoff_datetime)
            cutoff_index = \
                cls._MOST_RECENT_CONTACT_UPDATE_TIMESTAMP - cutoff_timestamp

            last_page_number_to_include = \
                ceil((cutoff_index + 1.0) / BATCH_RETRIEVAL_SIZE_LIMIT)
            first_contact_index_to_exclude = \
                int(last_page_number_to_include * BATCH_RETRIEVAL_SIZE_LIMIT)
            filtered_contacts = contacts[:first_contact_index_to_exclude]

        else:
            filtered_contacts = []

        return filtered_contacts

    def _get_query_string_args_for_page(self, page_number):
        super_ = super(GetAllContactsByLastUpdate, self)
        query_string_args_for_page = \
            super_._get_query_string_args_for_page(page_number)

        page_index = page_number - 1
        previous_page_contacts = self._objects_by_page[page_index - 1]
        previous_page_last_contact = previous_page_contacts[-1]
        query_string_args_for_page['timeOffset'] = \
            self._get_contact_added_at_timestamp(previous_page_last_contact)

        return query_string_args_for_page

    def _get_response_body_deserialization_for_page(self, page_contacts):
        super_ = super(GetAllContactsByLastUpdate, self)
        response_body_deserialization_for_page = \
            super_._get_response_body_deserialization_for_page(page_contacts)

        if page_contacts:
            page_last_contact = page_contacts[-1]
            time_offset = \
                self._get_contact_added_at_timestamp(page_last_contact)
        else:
            time_offset = 0
        response_body_deserialization_for_page['time-offset'] = time_offset

        return response_body_deserialization_for_page

    def _get_objects_data(self, contacts):
        contacts_data = \
            super(GetAllContactsByLastUpdate, self)._get_objects_data(contacts)

        for contact, contact_data in zip(contacts, contacts_data):
            contact_data['addedAt'] = \
                self._get_contact_added_at_timestamp(contact)

        return contacts_data

    @classmethod
    def get_contact_added_at_datetime(cls, contact, contacts):
        contact_index = contacts.index(contact)
        contact_added_at_timestamp = \
            cls._MOST_RECENT_CONTACT_UPDATE_TIMESTAMP - contact_index
        contact_added_at_datetime = \
            convert_timestamp_in_milliseconds_to_datetime(
                contact_added_at_timestamp,
                )
        return contact_added_at_datetime

    def _get_contact_added_at_timestamp(self, contact):
        contact_added_at_datetime = \
            self.get_contact_added_at_datetime(contact, self._contacts)
        contact_added_at_timestamp = \
            convert_date_to_timestamp_in_milliseconds(contact_added_at_datetime)
        return contact_added_at_timestamp


class SaveContacts(object):

    def __init__(self, contacts, available_properties):
        super(SaveContacts, self).__init__()

        self._contacts_by_page = paginate(contacts, BATCH_SAVING_SIZE_LIMIT)

        self._property_type_by_property_name = \
            {p.name: p.__class__ for p in available_properties}
        self._available_properties_simulator = \
            GetAllProperties(available_properties)

    def __call__(self):
        if not self._contacts_by_page:
            return []

        api_calls = self._available_properties_simulator()

        for batch_contacts in self._contacts_by_page:
            request_body_deserialization = format_contacts_data_for_saving(
                batch_contacts,
                self._property_type_by_property_name,
                )
            api_call = SuccessfulAPICall(
                CONTACTS_API_SCRIPT_NAME + '/contact/batch/',
                'POST',
                request_body_deserialization=request_body_deserialization,
                response_body_deserialization=None,
                )
            api_calls.append(api_call)

        return api_calls


class GetAllProperties(object):

    def __init__(self, properties):
        super(GetAllProperties, self).__init__()
        self._properties = properties

    def __call__(self):
        response_body_deserialization = \
            _format_response_data_for_properties(self._properties)
        get_all_properties_api_call = SuccessfulAPICall(
            CONTACTS_API_SCRIPT_NAME + '/properties',
            'GET',
            response_body_deserialization=response_body_deserialization,
            )
        return [get_all_properties_api_call]


class _BaseCreateProperty(object):

    __metaclass__ = ABCMeta

    def __init__(self, property_):
        super(_BaseCreateProperty, self).__init__()
        self._property = property_

    def __call__(self):
        api_call = self._get_api_call()
        return [api_call]

    @abstractmethod
    def _get_api_call(self):
        url_path = \
            CONTACTS_API_SCRIPT_NAME + '/properties/' + self._property.name
        property_data = format_data_for_property(self._property)
        api_call = APICall(
            url_path,
            'PUT',
            request_body_deserialization=property_data,
            )
        return api_call


class CreateProperty(_BaseCreateProperty):

    def _get_api_call(self):
        generalized_api_call = super(CreateProperty, self)._get_api_call()
        api_call = SuccessfulAPICall.init_from_generalization(
            generalized_api_call,
            response_body_deserialization=
                generalized_api_call.request_body_deserialization,
            )
        return api_call


class UnsuccessfulCreateProperty(_BaseCreateProperty):

    def __init__(self, property_, exception):
        super(UnsuccessfulCreateProperty, self).__init__(property_)
        self._exception = exception

    def _get_api_call(self):
        generalized_api_call = \
            super(UnsuccessfulCreateProperty, self)._get_api_call()
        api_call = UnsuccessfulAPICall.init_from_generalization(
            generalized_api_call,
            exception=self._exception,
            )
        return api_call


class DeleteProperty(object):

    def __init__(self, property_name):
        super(DeleteProperty, self).__init__()
        self._property_name = property_name

    def __call__(self):
        url_path = \
            CONTACTS_API_SCRIPT_NAME + '/properties/' + self._property_name
        api_call = SuccessfulAPICall(
            url_path,
            'DELETE',
            response_body_deserialization=None,
            )
        return [api_call]


class GetAllPropertyGroups(object):

    def __init__(self, property_groups):
        super(GetAllPropertyGroups, self).__init__()

        self._property_groups = property_groups

    def __call__(self):
        property_groups_data = []
        for property_group in self._property_groups:
            property_group_data = \
                _format_response_data_for_property_group(property_group)
            property_groups_data.append(property_group_data)

        api_call = SuccessfulAPICall(
            CONTACTS_API_SCRIPT_NAME + '/groups',
            'GET',
            response_body_deserialization=property_groups_data,
            )
        return [api_call]


class _BaseCreatePropertyGroup(object):

    __metaclass__ = ABCMeta

    def __init__(self, property_group):
        super(_BaseCreatePropertyGroup, self).__init__()

        self._property_group = property_group

    def __call__(self):
        api_call = self._get_api_call()
        return [api_call]

    @abstractmethod
    def _get_api_call(self):
        url_path = \
            CONTACTS_API_SCRIPT_NAME + '/groups/' + self._property_group.name
        request_body_deserialization = \
            format_request_data_for_property_group(self._property_group)
        api_call = APICall(
            url_path,
            'PUT',
            request_body_deserialization=request_body_deserialization,
            )
        return api_call


class CreatePropertyGroup(_BaseCreatePropertyGroup):

    def _get_api_call(self):
        generalized_api_call = super(CreatePropertyGroup, self)._get_api_call()

        response_body_deserialization = \
            _format_response_data_for_property_group(self._property_group)
        api_call = SuccessfulAPICall.init_from_generalization(
            generalized_api_call,
            response_body_deserialization=response_body_deserialization,
            )
        return api_call


class UnsuccessfulCreatePropertyGroup(_BaseCreatePropertyGroup):

    def __init__(self, property_group, exception):
        super(UnsuccessfulCreatePropertyGroup, self).__init__(property_group)

        self._exception = exception

    def _get_api_call(self):
        generalized_api_call = \
            super(UnsuccessfulCreatePropertyGroup, self)._get_api_call()
        api_call = UnsuccessfulAPICall.init_from_generalization(
            generalized_api_call,
            exception=self._exception,
            )
        return api_call


def _format_response_data_for_property_group(property_group):
    property_group_data = {
        'name': property_group.name,
        'displayName': property_group.display_name or '',
        'displayOrder': 1,
        'portalId': 1,
        }
    if property_group.properties:
        property_group_data['properties'] = \
            _format_response_data_for_properties(property_group.properties)
    return property_group_data


def _format_response_data_for_properties(properties):
    properties_data = [format_data_for_property(p) for p in properties]
    return properties_data


class DeletePropertyGroup(object):

    def __init__(self, property_group_name):
        super(DeletePropertyGroup, self).__init__()
        self._property_group_name = property_group_name

    def __call__(self):
        url_path = \
            CONTACTS_API_SCRIPT_NAME + '/groups/' + self._property_group_name
        api_call = SuccessfulAPICall(
            url_path,
            'DELETE',
            response_body_deserialization=None,
            )
        return [api_call]


class GetAllContactLists(_PaginatedObjectsRetriever):

    _API_CALL_PATH_INFO = '/lists'

    _OBJECT_DATA_KEY = 'lists'

    def _get_query_string_args_for_page(self, page_number):
        query_string_args_for_page = \
            {'offset': BATCH_RETRIEVAL_SIZE_LIMIT * (page_number - 1)}
        return query_string_args_for_page

    def _get_response_body_deserialization_for_page(self, page_contact_lists):
        page_number = self._get_current_objects_page_number(page_contact_lists)
        response_body_deserialization_for_page = {
            'offset': BATCH_RETRIEVAL_SIZE_LIMIT * page_number,
            }
        return response_body_deserialization_for_page

    @staticmethod
    def _get_objects_data(contact_lists):
        contact_lists_data = []
        for contact_list in contact_lists:
            contact_list_data = {
                'listId': contact_list.id,
                'name': contact_list.name,
                'dynamic': contact_list.is_dynamic,
                }
            contact_lists_data.append(contact_list_data)
        return contact_lists_data


class _BaseCreateStaticContactList(object):

    __metaclass__ = ABCMeta

    def __init__(self, contact_list_name):
        super(_BaseCreateStaticContactList, self).__init__()
        self._contact_list_name = contact_list_name

    def __call__(self):
        api_call = self._get_api_call()
        return [api_call]

    @abstractmethod
    def _get_api_call(self):
        request_body_deserialization = {
            'name': self._contact_list_name,
            'dynamic': False,
            }
        api_call = APICall(
            CONTACTS_API_SCRIPT_NAME + '/lists',
            'POST',
            request_body_deserialization=request_body_deserialization,
            )
        return api_call


class CreateStaticContactList(_BaseCreateStaticContactList):

    def _get_api_call(self):
        generalized_api_call = \
            super(CreateStaticContactList, self)._get_api_call()

        response_body_deserialization = \
            dict(generalized_api_call.request_body_deserialization, listId=1)

        api_call = SuccessfulAPICall.init_from_generalization(
            generalized_api_call,
            response_body_deserialization=response_body_deserialization,
            )
        return api_call


class UnsuccessfulCreateStaticContactList(_BaseCreateStaticContactList):

    def __init__(self, contact_list_name, exception):
        super_ = super(UnsuccessfulCreateStaticContactList, self)
        super_.__init__(contact_list_name)
        self._exception = exception

    def _get_api_call(self):
        generalized_api_call = \
            super(UnsuccessfulCreateStaticContactList, self)._get_api_call()

        api_call = UnsuccessfulAPICall.init_from_generalization(
            generalized_api_call,
            exception=self._exception,
            )
        return api_call


class DeleteContactList(object):

    def __init__(self, contact_list_id):
        super(DeleteContactList, self).__init__()
        self._contact_list_id = contact_list_id

    def __call__(self):
        url_path = '{}/lists/{}'.format(
            CONTACTS_API_SCRIPT_NAME,
            self._contact_list_id,
            )
        api_call = SuccessfulAPICall(
            url_path,
            'DELETE',
            response_body_deserialization=None,
            )
        return [api_call]


class _UpdateContactListMembership(object):

    __metaclass__ = ABCMeta

    url_path_list_action = abstractproperty()

    def __init__(self, contact_list, contacts_to_update, updated_contacts):
        super(_UpdateContactListMembership, self).__init__()
        self._contact_list = contact_list
        self._contacts_to_update_vids = \
            self._get_contact_vids(contacts_to_update)
        self._updated_contacts_vids = self._get_contact_vids(updated_contacts)

    def __call__(self):
        if not self._contacts_to_update_vids:
            return []

        request_body_deserialization = {'vids': self._contacts_to_update_vids}
        response_body_deserialization = {'updated': self._updated_contacts_vids}
        path_info = '/lists/{}/{}'.format(
            self._contact_list.id,
            self.url_path_list_action,
            )
        api_call = SuccessfulAPICall(
            CONTACTS_API_SCRIPT_NAME + path_info,
            'POST',
            request_body_deserialization=request_body_deserialization,
            response_body_deserialization=response_body_deserialization,
            )
        return [api_call]

    @staticmethod
    def _get_contact_vids(contacts):
        return [c.vid for c in contacts]


class AddContactsToList(_UpdateContactListMembership):

    url_path_list_action = 'add'

    def __init__(self, contact_list, contacts_to_add, updated_contacts):
        super(AddContactsToList, self).__init__(
            contact_list,
            contacts_to_add,
            updated_contacts,
            )


class RemoveContactsFromList(_UpdateContactListMembership):

    url_path_list_action = 'remove'

    def __init__(self, contact_list, contacts_to_remove, updated_contacts):
        super(RemoveContactsFromList, self).__init__(
            contact_list,
            contacts_to_remove,
            updated_contacts,
            )

class GetContactsFromList(GetAllContacts):

    _API_CALL_PATH_INFO_TEMPLATE = '/lists/{}/contacts/all'

    def __init__(
        self,
        contact_list,
        contacts,
        available_properties,
        property_names=(),
        ):
        super_ = super(GetContactsFromList, self)
        super_.__init__(contacts, available_properties, property_names)

        self._contact_list = contact_list

    @property
    def _API_CALL_PATH_INFO(self):
        return self._API_CALL_PATH_INFO_TEMPLATE.format(self._contact_list.id)
