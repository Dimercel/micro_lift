from datetime import datetime as dt

from marshmallow import Schema, fields


ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class Lift(Schema):
    id = fields.Str()
    speed = fields.Float(required=True)
    max_weight = fields.Int(required=True)
    position = fields.Float(default=0.0)
    passengers = fields.List(fields.Str(), default=[])


class Actor(Schema):
    uid = fields.Str(required=True)
    weight = fields.Float(required=True)
    timestamp = fields.DateTime(ISO8601_FORMAT, missing=lambda: dt.utcnow())
