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

from datetime import date
from inspect import isgenerator
from itertools import islice
from time import mktime as convert_timetuple_to_timestamp

from hubspot.contacts.exc import HubspotPropertyValueError


def ipaginate(iterable, page_size):
    if not isgenerator(iterable):
        iterable = iter(iterable)

    next_page_iterable = _get_next_page_iterable_as_list(iterable, page_size)
    while next_page_iterable:
        yield next_page_iterable

        next_page_iterable = \
            _get_next_page_iterable_as_list(iterable, page_size)


def _get_next_page_iterable_as_list(iterable, page_size):
    next_page_iterable = list(islice(iterable, page_size))
    return next_page_iterable


def convert_date_to_timestamp_in_milliseconds(datetime_or_date):
    if not isinstance(datetime_or_date, date):
        raise HubspotPropertyValueError(
            '{!r} is not a date'.format(datetime_or_date),
            )

    timestamp = _convert_datetime_to_timestamp(datetime_or_date)
    datetime_milliseconds = getattr(datetime_or_date, 'microsecond', 0) / 1000
    date_timestamp_in_milliseconds = timestamp * 1000 + datetime_milliseconds
    return date_timestamp_in_milliseconds


def _convert_datetime_to_timestamp(datetime_):
    timetuple = datetime_.timetuple()
    timestamp = convert_timetuple_to_timestamp(timetuple)
    timestamp = int(timestamp)
    return timestamp
