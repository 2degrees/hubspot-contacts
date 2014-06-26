Python Library to Manage Contacts via the HubSpot API
=====================================================

.. image:: https://travis-ci.org/2degrees/hubspot-contacts.svg?branch=master
    :target: https://travis-ci.org/2degrees/hubspot-contacts
    :align: right

.. image:: https://coveralls.io/repos/2degrees/hubspot-contacts/badge.png?branch=master
    :target: https://coveralls.io/r/2degrees/hubspot-contacts?branch=master
    :align: right

:Download: `<http://pypi.python.org/pypi/hubspot-contacts>`_
:Sponsored by: `2degrees Limited <http://dev.2degreesnetwork.com/>`_.

**hubspot-contacts** is a high-level, Pythonic wrapper for `HubSpot API
<http://developers.hubspot.com/docs/endpoints>`_ methods in the `Contacts
<http://developers.hubspot.com/docs/endpoints#contacts-api>`_, `Contact Lists
<http://developers.hubspot.com/docs/endpoints#contact-lists-api>`_ and
`Contact Properties
<http://developers.hubspot.com/docs/endpoints#contact-properties-api>`_ APIs.

Here's an example of how it can be used::

    >>> from hubspot.connection import APIKey, PortalConnection
    >>> from hubspot.contacts import Contact
    >>> from hubspot.contacts.lists import get_all_contacts
    >>> 
    >>> authentication_key = APIKey("your key")
    >>> 
    >>> with PortalConnection(authentication_key, "Your App Name") as connection:
    ...     for contact in get_all_contacts(connection):
    ...         print contact
    ... 
    Contact(vid=1, email_address=u'foo@example.com', properties={u'lastname': u'Smith', u'company': u'ACME Ltd.', u'firstname': u'John', u'lastmodifieddate': datetime.datetime(2014, 5, 30, 15, 32, 7, 192000)}, related_contact_vids=[])
    Contact(vid=2, email_address=u'bar@example.com', properties={u'lastname': u'Doe', u'company': u'Example Inc.', u'firstname': u'Alice', u'lastmodifieddate': datetime.datetime(2014, 5, 29, 15, 37, 52, 447000)}, related_contact_vids=[])

This project is officially supported under Python 2.7, but may work with
Python 2.6 and Python 3.

**hubspot-contacts** depends on `hubspot-connection
<http://pythonhosted.org/hubspot-connection>`_, a separate library
that abstracts the low-level communication with HubSpot and takes care of
authentication, among other things.
