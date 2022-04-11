from datetime import datetime as dt
from functools import wraps

from marshmallow import Schema, ValidationError
from marshmallow import fields
from marshmallow import validate
from marshmallow.validate import Range
from marshmallow_enum import EnumField

from models import ActorStatus, LiftStatus

ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def with_schema(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(self, _, __, data, *args, **kwargs):
            valid_data = schema().load(data)

            return func(self, _, __, valid_data, *args, **kwargs)

        return wrapper
    return decorator


def _validate_iso8601(value):
    try:
        dt.strptime(value, ISO8601_FORMAT)
    except ValueError:
        raise ValidationError(f"'{value}' is not correct ISO 8601 value")


class IncomingSchema(Schema):
    signal = fields.Str(required=True)
    id = fields.Str(default=None, missing=None, allow_none=True, validate=validate.Length(max=32))
    data = fields.Dict(required=True)


class AuthSchema(Schema):
    uid = fields.Str(required=True)
    timestamp = fields.Str(required=True, validate=_validate_iso8601)
    token = fields.Str(required=True)
    weight = fields.Float(required=True, validate=validate.Range(min=1.0))


class LiftListSchema(Schema):
    count = fields.Int(default=10, missing=10, validate=Range(min=1))


class ActorListSchema(Schema):
    count = fields.Int(default=10, missing=10, validate=Range(min=1))


class ActorExpectSchema(Schema):
    floor = fields.Int(required=True, validate=Range(min=1))

class Actor(Schema):
    uid = fields.Str(required=True)
    weight = fields.Float(required=True)
    floor = fields.Int(default=1, missing=1, allow_none=True)
    need_floor = fields.Int(default=None, missing=None, allow_none=True)
    status = EnumField(ActorStatus, load_by=EnumField.VALUE,
                       default=ActorStatus.IDLE, missing=ActorStatus.IDLE)
    timestamp = fields.DateTime(ISO8601_FORMAT, missing=lambda: dt.utcnow())

class Lift(Schema):
    id = fields.Str()
    speed = fields.Float(required=True)
    max_weight = fields.Int(required=True)
    position = fields.Float(default=0.0)
    passengers = fields.List(fields.Str(), default=[], missing=[])
    status = EnumField(LiftStatus, load_by=EnumField.VALUE,
                       missing=LiftStatus.STOPPED, default=LiftStatus.STOPPED)
