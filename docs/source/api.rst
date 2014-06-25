API Documentation
=================

Keep the following in mind while using the functions provided by this library:

- You should only use the connection from a context manager so that any startup
  or shutdown routine can be executed.
- Date and datetime objects are timezone-naive but should still match the
  timezone used by HubSpot (UTC as at this writing).
- When HubSpot fails to process a request made by any of the functions in this
  library, **hubspot-connection** will raise an exception that sub-classes
  :exc:`hubspot.connection.exc.HubspotException`.


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

.. class:: Property

    Base class for a HubSpot property.
    
    The following attributes correspond to the same data associated to a
    particular property on HubSpot.
    
    .. attribute:: name
    
    .. attribute:: label
    
    .. attribute:: description
    
    .. attribute:: group_name
    
    .. attribute:: field_widget
    
        HubSpot usually refers to this as the "field type", even though it
        isn't strictly do to with data types. Instead, this attribute refers
        to the type of widget to be used when displaying/capturing the property
        value (e.g., a date picker for a :class:`DateProperty`).


.. class:: BooleanProperty

    :bases: :class:`Property`
    
    .. attribute:: true_label
        
        The user-friendly string to refer to property value ``True`` when
        presented on HubSpot. By default, this is ``"Yes"``.
    
    .. attribute:: false_label
        
        The user-friendly string to refer to property value ``False`` when
        presented on HubSpot. By default, this is ``"No"``.
    

.. class:: DateProperty

    :bases: :class:`Property`

.. class:: DatetimeProperty

    :bases: :class:`Property`

.. class:: EnumerationProperty

    :bases: :class:`Property`

    The definition of an enum(eration) property.
    
    .. attribute:: options
    
        A mapping with all the possible values for the enumeration.
        
        The mapping keys are the property values and the mapping values are
        the user-friendly labels for each property value. For example::
        
            {'gbp': 'Pound Sterling', 'eur': 'Euro', 'usd': 'US Dollar'}
        

.. class:: NumberProperty

    :bases: :class:`Property`

.. class:: StringProperty

    :bases: :class:`Property`


Property Groups
~~~~~~~~~~~~~~~

.. module:: hubspot.contacts.property_groups

.. autofunction:: get_all_property_groups

.. autofunction:: create_property_group

.. autofunction:: delete_property_group


Supported Datatypes
^^^^^^^^^^^^^^^^^^^

.. autoclass:: PropertyGroup
