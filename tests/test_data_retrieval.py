from nose.tools import assert_dict_contains_subset
from nose.tools import assert_in
from nose.tools import assert_not_in
from nose.tools import assert_raises
from nose.tools import eq_
from voluptuous import Invalid
from hubspot.connection.testing import MockPortalConnection
from hubspot.connection.testing import RemoteMethod

from hubspot.contacts._data_retrieval import PaginatedDataRetriever


_STUB_DUDE_A = 'Dude A'

_STUB_DUDE_B = 'Dude B'


class TestPaginatedDataRetriever(object):

    def test_no_data(self):
        expected_data = []

        connection = self._make_connection_for_pages(expected_data)

        data_retriever = PaginatedDataRetriever(
            response_data_key='dudes',
            response_offset_keys=['dude-offset'],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')
        retrieved_data = list(retrieved_data)

        eq_(expected_data, retrieved_data)

    def test_extra_url_params(self):
        expected_url_params = {'bla': 1}

        connection = self._make_connection_for_pages([])

        data_retriever = PaginatedDataRetriever(
            response_data_key='dudes',
            response_offset_keys=['dude-offset'],
            )
        retrieved_data = \
            data_retriever.get_data(connection, '/dudes', expected_url_params)
        retrieved_data = list(retrieved_data)

        invocation = connection.remote_method_invocations[0]
        query_string_args = invocation.query_string_args
        assert_dict_contains_subset(expected_url_params, query_string_args)

    def test_page_size(self):
        connection = self._make_connection_for_pages([])

        data_retriever = PaginatedDataRetriever(
            page_size=23,
            response_data_key='dudes',
            response_offset_keys=['dude-offset'],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')
        retrieved_data = list(retrieved_data)

        invocation = connection.remote_method_invocations[0]
        query_string_args = invocation.query_string_args
        assert_dict_contains_subset({'count': 23}, query_string_args)

    def test_single_page_data(self):
        expected_data = ['dude']

        connection = self._make_connection_for_pages(expected_data)

        data_retriever = PaginatedDataRetriever(
            page_size=1,
            response_data_key='dudes',
            response_offset_keys=['dude-offset'],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')
        retrieved_data = list(retrieved_data)

        eq_(1, len(connection.remote_method_invocations))
        eq_(expected_data, retrieved_data)

    def test_multi_page_data(self):
        connection = self._make_connection_for_multiple_pages()

        data_retriever = PaginatedDataRetriever(
            page_size=1,
            response_data_key='dudes',
            response_offset_keys=['dude-offset'],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')
        retrieved_data = list(retrieved_data)

        eq_(2, len(connection.remote_method_invocations))
        eq_([_STUB_DUDE_A, _STUB_DUDE_B], retrieved_data)

    def test_multi_page_data_one_page_consumed(self):
        connection = self._make_connection_for_multiple_pages()

        data_retriever = PaginatedDataRetriever(
            page_size=1,
            response_data_key='dudes',
            response_offset_keys=['dude-offset'],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')

        next(retrieved_data)

        eq_(1, len(connection.remote_method_invocations))

    def test_offset_response_keys(self):
        response_data_1 = {
            'has-more': True,
            'vid-offset': 1,
            'dude-offset': 2,
            'dudes': ['dude_A'],
            }
        response_data_2 = {
            'has-more': False,
            'vid-offset': 2,
            'dude-offset': 6,
            'dudes': ['dude_B'],
            }
        response_data_maker = _ConstantMultipleResponseDataMaker([
            response_data_1,
            response_data_2,
            ])
        connection = MockPortalConnection({
            RemoteMethod('/dudes', 'GET'): response_data_maker,
            })

        data_retriever = PaginatedDataRetriever(
            page_size=1,
            response_data_key='dudes',
            response_offset_keys=['vid-offset', 'dude-offset'],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')
        retrieved_data = list(retrieved_data)

        invocations = connection.remote_method_invocations

        query_string_args = invocations[0].query_string_args
        assert_not_in('vidOffset', query_string_args)
        assert_not_in('dudeOffset', query_string_args)

        query_string_args = invocations[1].query_string_args
        assert_in('vidOffset', query_string_args)
        assert_in('dudeOffset', query_string_args)

    def test_response_data_key_not_found_in_response(self):
        connection = self._make_connection_for_multiple_pages()

        data_retriever = PaginatedDataRetriever(
            page_size=1,
            response_data_key='dudettes',
            response_offset_keys=[],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')
        with assert_raises(Invalid):
            list(retrieved_data)

    def test_response_offset_key_not_found_in_response(self):
        connection = self._make_connection_for_multiple_pages()

        data_retriever = PaginatedDataRetriever(
            page_size=1,
            response_data_key='dudes',
            response_offset_keys=['dd-offset'],
            )
        retrieved_data = data_retriever.get_data(connection, '/dudes')
        with assert_raises(Invalid):
            list(retrieved_data)

    def _make_connection_for_pages(self, *pages_data):
        responses_data = []
        for i, page_data in enumerate(pages_data):
            response_data = {
                'has-more': True,
                'dude-offset': i,
                'dudes': page_data,
                }
            responses_data.append(response_data)

        if responses_data:
            responses_data[-1]['has-more'] = False

        response_data_maker = _ConstantMultipleResponseDataMaker(responses_data)
        connection = MockPortalConnection({
            RemoteMethod('/dudes', 'GET'): response_data_maker,
            })
        return connection

    def _make_connection_for_multiple_pages(self):
        return self._make_connection_for_pages([_STUB_DUDE_A], [_STUB_DUDE_B])


class _ConstantMultipleResponseDataMaker(object):

    def __init__(self, responses_data):
        self._responses_data = iter(responses_data)

    def __call__(self, query_string_args, body_deserialization):
        response_data = next(self._responses_data)
        return response_data

