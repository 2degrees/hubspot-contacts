from voluptuous import Schema


CONTACT_LIST_SCHEMA = Schema(
    {
        'listId': int,
        'name': unicode,
        'dynamic': bool,
        },
    required=True,
    extra=True,
    )
