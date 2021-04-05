from marshmallow import Schema, fields


ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class Lift(Schema):
    id = fields.Str()
    speed = fields.Float(required=True)
    max_weight = fields.Int(required=True)
    position = fields.Float(default=0)


class Actor(Schema):
    uid = fields.StrField(required=True)
    last_auth = fields.DateTimeField(ISO8601_FORMAT, default=None, allow_none=True)
