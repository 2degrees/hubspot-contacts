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
from abc import ABCMeta
from abc import abstractproperty

from pyrecord import Record


RemoteMethod = Record.create_type('RemoteMethod', 'path_info', 'http_method')


class BaseMethodTestCase(object):

    __metaclass__ = ABCMeta

    _REMOTE_METHOD = abstractproperty()

    @classmethod
    def _assert_expected_remote_method_used(cls, connection):
        connection.assert_requested_path_infos_equal(
            cls._REMOTE_METHOD.path_info,
            )
        connection.assert_request_methods_equal(cls._REMOTE_METHOD.http_method)
