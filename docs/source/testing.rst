Testing Tutorial
================

**hubspot-connection** offers utilities to simulate communication with HubSpot,
thus allowing you to unit test your code on top of **hubspot-contacts**.

Imagine that you'd like to write unit tests for the function below::

    from hubspot.contacts.lists import get_contact_lists
    
    def get_contact_list_names(connection):
        return [list_.name for list_ in get_contact_lists(connection)]

One of the cases that you'd like to test would be when there's exactly one
list. You'd test this unit by passing a so-called "mock portal connection"
instead of a regular portal connection; e.g.::

    from hubspot.connection.testing import MockPortalConnection
    from hubspot.contacts.lists import ContactList
    from hubspot.contacts.testing import GetAllContactLists

    def test_one_list():
        contact_list = ContactList(id=1, name='Your List', is_dynamic=False)
        simulator = GetAllContactLists([contact_list])
        with MockPortalConnection(simulator) as connection:
            contact_list_names = get_contact_list_names(connection)
            
        assert len(contact_list_names) == 1
        assert contact_list_names[0] == contact_list.name

The mock portal connection is initialized with zero or more so-called "api
call simulators" (or simply "simulators"), which are passed by position. The
purpose of a simulator is twofold:

- One the one hand, it tells the connection what exactly you expect will get
  sent to HubSpot. If the wrong API end-point is called or the right one is
  called with the wrong arguments, an ``AssertionError`` would be raised by the
  connection.
- On the other hand, you can use it to forge the response that HubSpot would
  give to a particular request. In the example above, we replicated the case
  where HubSpot responded that there were no contact lists in the portal.

By using the mock portal connection as a context manager, you also ensure that
all of the specified API end-points are called and nothing else.

Read :mod:`hubspot.connection.testing` to learn more about the mock portal
connection, or read on to learn about the individual simulators provided by
this library.


Simulators
----------

Each of the end-points supported by this library ship with a simulator for
cases where the request completes successfully. In some cases, a simulator for
error cases is also provided; their constructors largely share the same
signature as their successful counterparts, but they also require the exception
instance that is expected to be raised.

.. module:: hubspot.contacts.testing

.. autoclass:: GetAllContacts

.. autoclass:: GetAllContactsByLastUpdate

.. autoclass:: SaveContacts

.. class:: UnsuccessfulGetAllContacts

    The unsuccessful counterpart to :class:`GetAllContacts`.
    
    .. method:: __init__(contacts, exception, *args, **kwargs)
    
        The additional arguments are passed to :class:`GetAllContacts`.

.. class:: UnsuccessfulGetAllContactsByLastUpdate

    The unsuccessful counterpart to :class:`GetAllContactsByLastUpdate`.
    
    .. method:: __init__(contacts, exception, *args, **kwargs)
    
        The additional arguments are passed to
        :class:`GetAllContactsByLastUpdate`.

.. autoclass:: UnsuccessfulSaveContacts


Contact Lists
~~~~~~~~~~~~~

.. autoclass:: GetAllContactLists

    .. method:: __init__(contact_lists)
    
        :param iterable contact_lists:
            :class:`~hubspot.contacts.lists.ContactList` instances for all the
            contact lists supposedly in the portal

.. autoclass:: CreateStaticContactList

.. autoclass:: GetContactsFromList

.. autoclass:: GetContactsFromListByAddedDate

.. autoclass:: DeleteContactList

.. autoclass:: AddContactsToList

.. autoclass:: RemoveContactsFromList

.. autoclass:: UnsuccessfulCreateStaticContactList


Contact Properties
~~~~~~~~~~~~~~~~~~

.. autoclass:: GetAllProperties

.. autoclass:: CreateProperty

.. autoclass:: DeleteProperty

.. autoclass:: UnsuccessfulCreateProperty


Contact Property Groups
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: GetAllPropertyGroups

.. autoclass:: CreatePropertyGroup

.. autoclass:: DeletePropertyGroup

.. autoclass:: UnsuccessfulCreatePropertyGroup
