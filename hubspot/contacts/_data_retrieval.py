import re

from voluptuous import Schema

from hubspot.contacts._constants import BATCH_RETRIEVAL_SIZE_LIMIT


_CAMEL_CASE_CONVERSION_RE = re.compile(r'\-(\w)')


class PaginatedDataRetriever(object):

    def __init__(
        self,
        response_data_key,
        response_offset_keys,
        page_size=BATCH_RETRIEVAL_SIZE_LIMIT,
        ):
        self._response_data_key = response_data_key
        self._response_offset_keys = response_offset_keys
        self._page_size = page_size

        self._offset_url_param_name_by_response_key = \
            {k: _convert_to_camel_case(k) for k in self._response_offset_keys}

        self._schema = self._get_response_data_schema()

    def get_data(self, connection, path_info, query_string_args=None):
        data_by_page = \
            self._get_data_by_page(path_info, query_string_args, connection)
        for page_data in data_by_page:
            for datum in page_data:
                yield datum

    def _get_data_by_page(self, path_info, query_string_args, connection):
        if query_string_args:
            base_query_string_args = query_string_args.copy()
        else:
            base_query_string_args = {}

        if self._page_size:
            base_query_string_args['count'] = self._page_size

        has_more_pages = True
        next_request_offset_query_string_args = {}
        while has_more_pages:
            query_string_args = base_query_string_args.copy()
            query_string_args.update(next_request_offset_query_string_args)

            response = connection.send_get_request(path_info, query_string_args)
            response = self._validate_response_data(response)

            response_data = response[self._response_data_key]
            yield response_data

            next_request_offset = \
                _filter_dict(response, self._response_offset_keys)
            next_request_offset_query_string_args = _translate_dict_keys(
                next_request_offset,
                self._offset_url_param_name_by_response_key,
                )

            has_more_pages = response['has-more']

    def _validate_response_data(self, response_data):
        return self._schema(response_data)

    def _get_response_data_schema(self):
        schema_definition = {k: int for k in self._response_offset_keys}
        schema_definition['has-more'] = bool
        schema_definition[self._response_data_key] = []
        page_data_schema = Schema(schema_definition, required=True)
        return page_data_schema


#{ Utils


def _convert_to_camel_case(string):
    uppercase_matched_group = lambda m: m.groups()[0].upper()
    return _CAMEL_CASE_CONVERSION_RE.sub(uppercase_matched_group, string)


def _translate_dict_keys(dict_, translation_dict):
    return {translation_dict[k]: v for k, v in dict_.items()}


def _filter_dict(dict_, keys):
    return {k: dict_[k] for k in keys}
