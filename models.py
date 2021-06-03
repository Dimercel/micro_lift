from datetime import datetime as dt
from enum import Enum

from marshmallow import Schema, fields
from marshmallow_enum import EnumField


ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class LiftStatus(Enum):
    STOPPED = 0
    IN_ACTION = 1


class ActorStatus(Enum):
    SLEEP = 0
    EXPECT = 1
    IN_LIFT = 2


class Lift(Schema):
    id = fields.Str()
    speed = fields.Float(required=True)
    max_weight = fields.Int(required=True)
    position = fields.Float(default=0.0)
    passengers = fields.List(fields.Str(), default=[])
    status = EnumField(LiftStatus, load_by=EnumField.VALUE, default=LiftStatus.STOPPED)


class Actor(Schema):
    uid = fields.Str(required=True)
    weight = fields.Float(required=True)
    stage = fields.Int(default=1, missing=1, allow_none=True)
    need_stage = fields.Int(default=None, missing=None, allow_none=True)
    status = EnumField(ActorStatus, load_by=EnumField.VALUE,
                       default=ActorStatus.SLEEP, missing=ActorStatus.SLEEP)
    timestamp = fields.DateTime(ISO8601_FORMAT, missing=lambda: dt.utcnow())
