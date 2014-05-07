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
from datetime import datetime
from datetime import timedelta
from inspect import isgenerator
from itertools import islice
from uuid import uuid4 as get_uuid4

from hubspot.contacts.exc import HubspotPropertyValueError


_EPOCH_DATETIME = datetime(1970, 1, 1)

_EPOCH_DATE = date.fromordinal(_EPOCH_DATETIME.toordinal())


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


def convert_timestamp_in_milliseconds_to_datetime(timestamp_milliseconds):
    timestamp_milliseconds = int(timestamp_milliseconds)
    time_since_epoch = timedelta(milliseconds=timestamp_milliseconds)
    timestamp_as_datetime = _EPOCH_DATETIME + time_since_epoch
    return timestamp_as_datetime


def convert_timestamp_in_milliseconds_to_date(timestamp_milliseconds):
    timestamp_datetime = \
        convert_timestamp_in_milliseconds_to_datetime(timestamp_milliseconds)
    timestamp_date = timestamp_datetime.date()
    return timestamp_date


def paginate(iterable, page_size):
    return list(ipaginate(iterable, page_size))


def convert_date_to_timestamp_in_milliseconds(datetime_or_date):
    timestamp = _convert_datetime_to_timestamp(datetime_or_date)
    date_timestamp_in_milliseconds = int(timestamp * 1000)
    return date_timestamp_in_milliseconds


def _convert_datetime_to_timestamp(datetime_or_date):
    if not isinstance(datetime_or_date, date):
        raise HubspotPropertyValueError(
            '{!r} is not a date'.format(datetime_or_date),
            )

    if isinstance(datetime_or_date, datetime):
        epoch = _EPOCH_DATETIME
    else:
        epoch = _EPOCH_DATE
    time_since_epoch = datetime_or_date - epoch
    timestamp = time_since_epoch.total_seconds()
    return timestamp


def get_uuid4_str():
    uuid4 = get_uuid4()
    return str(uuid4)
