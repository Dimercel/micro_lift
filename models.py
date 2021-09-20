from datetime import datetime as dt
from enum import Enum
from math import ceil

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
    passengers = fields.List(fields.Str(), default=[], missing=[])
    status = EnumField(LiftStatus, load_by=EnumField.VALUE,
                       missing=LiftStatus.STOPPED, default=LiftStatus.STOPPED)

    def __init__(self, floor_height=1.0, *args, **kwargs):
        self._floor_height = floor_height

        super().__init__(*args, **kwargs)

    @property
    def floor(self):
        return ceil(self.position / self._floor_height)

    def near_drop_floor(self):
        """Ближайший этаж, на котором нужно высадить пассажира"""

        cur_floor = self.floor
        dist = [(abs(cur_floor - x.need_floor), x.need_floor) for x in self.passengers]
        min(dist, key=lambda x: x[0])[1] if self.passengers and dist else cur_floor

    def stop(self):
        self.status = LiftStatus.STOPPED

    def move_up(self):
        self.position += self.speed

    def move_down(self):
        self.position -= self.speed

        if self.position < 0:
            self.position = 0

    def is_empty(self):
        return not self.passengers


class Actor(Schema):
    uid = fields.Str(required=True)
    weight = fields.Float(required=True)
    floor = fields.Int(default=1, missing=1, allow_none=True)
    need_floor = fields.Int(default=None, missing=None, allow_none=True)
    status = EnumField(ActorStatus, load_by=EnumField.VALUE,
                       default=ActorStatus.SLEEP, missing=ActorStatus.SLEEP)
    timestamp = fields.DateTime(ISO8601_FORMAT, missing=lambda: dt.utcnow())

    def move_to_floor(self, floor):
        if floor != self.floor:
            self.need_floor = floor
            self.status = ActorStatus.EXPECT
