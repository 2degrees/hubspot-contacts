API Documentation
=================

Contacts API
------------

The following methods from the `Contacts API
<http://developers.hubspot.com/docs/endpoints#contacts-api>`_ are currently
supported:


.. autofunction:: hubspot.contacts.lists.get_all_contacts


.. autofunction:: hubspot.contacts.lists.get_all_contacts_by_last_update


.. autofunction:: hubspot.contacts.save_contacts


Entities
~~~~~~~~

.. autoclass:: hubspot.contacts.Contact
    
    A HubSpot contact.
    
    .. attribute:: vid
        
        An :class:`int` instance for the contact's identifier on HubSpot.
    
    .. attribute:: email_address
        
        The contact's email address as a :class:`unicode` string or ``None``
        if unknown.
    
    .. attribute:: properties
        
        A dictionary with the values associated to the contact.
    
    .. attribute:: related_contact_vids = ()
        
        The VIDs for each of the contacts related to the current one.


Contact Lists API
-----------------

.. note::

    Only static lists are supported at this moment.

The following methods from the `Contact Lists API
<http://developers.hubspot.com/docs/endpoints#contact-lists-api>`_ are currently
supported:


.. autofunction:: hubspot.contacts.lists.get_all_contact_lists

.. autofunction:: hubspot.contacts.lists.create_static_contact_list

.. autofunction:: hubspot.contacts.lists.delete_contact_list

.. autofunction:: hubspot.contacts.lists.get_all_contacts_from_list

.. autofunction:: hubspot.contacts.lists.get_all_contacts_from_list_by_added_date

.. autofunction:: hubspot.contacts.lists.add_contacts_to_list

.. autofunction:: hubspot.contacts.lists.remove_contacts_from_list


Entities
~~~~~~~~

.. class:: hubspot.contacts.lists.ContactList

    A HubSpot contact list.

    .. attribute:: id
    
    .. attribute:: name

    .. attribute:: is_dynamic
    
        Whether the list is dynamic.


Contact Properties API
----------------------

The following methods from the `Contact Properties API
<http://developers.hubspot.com/docs/endpoints#contact-properties-api>`_ are
currently supported:


Properties
~~~~~~~~~~

.. module:: hubspot.contacts.properties

.. autofunction:: get_all_properties

.. autofunction:: create_property

.. autofunction:: delete_property


Supported Datatypes
^^^^^^^^^^^^^^^^^^^

.. autoclass:: Property

.. autoclass:: BooleanProperty

.. autoclass:: DateProperty

.. autoclass:: DatetimeProperty

.. autoclass:: EnumerationProperty

.. autoclass:: NumberProperty

.. autoclass:: StringProperty


Property Groups
~~~~~~~~~~~~~~~

.. module:: hubspot.contacts.property_groups

.. autofunction:: get_all_property_groups

.. autofunction:: create_property_group

.. autofunction:: delete_property_group


Supported Datatypes
^^^^^^^^^^^^^^^^^^^

.. autoclass:: PropertyGroup


Exceptions raised by **hubspot-connection**
-------------------------------------------

When HubSpot fails to process a request made by any of the functions in this
library, **hubspot-connection** will raise an exception that sub-classes
:exc:`hubspot.connection.exc.HubspotException`.
