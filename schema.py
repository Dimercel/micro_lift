from functools import wraps

from marshmallow import Schema, fields


ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def with_schema(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(self, _, data, *args, **kwargs):
            valid_data = schema().load(data)

            return func(self, _, valid_data, *args, **kwargs)

        return wrapper
    return decorator


class AuthSchema(Schema):
    uid = fields.Str(required=True)
    timestamp = fields.DateTime(ISO8601_FORMAT, required=True)
    token = fields.Str(required=True)
    weight = fields.Float(required=True)
