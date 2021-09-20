from datetime import datetime
from functools import wraps

from marshmallow import Schema, ValidationError
from marshmallow import fields
from marshmallow.validate import Range


ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def with_schema(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(self, _, data, *args, **kwargs):
            valid_data = schema().load(data)

            return func(self, _, valid_data, *args, **kwargs)

        return wrapper
    return decorator


def _validate_iso8601(value):
    try:
        datetime.strptime(value, ISO8601_FORMAT)
    except ValueError:
        raise ValidationError(f"'{value}' is not correct ISO 8601 value")


class AuthSchema(Schema):
    uid = fields.Str(required=True)
    timestamp = fields.Str(required=True, validate=_validate_iso8601)
    token = fields.Str(required=True)
    weight = fields.Float(required=True)


class LiftListSchema(Schema):
    count = fields.Int(default=10, missing=10, validate=Range(min=1))


class ActorListSchema(Schema):
    count = fields.Int(default=10, missing=10, validate=Range(min=1))


class ActorExpectSchema(Schema):
    floor = fields.Int(required=True, validate=Range(min=1))
