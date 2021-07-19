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

    def __init__(self, stage_height, *args, **kwargs):
        self._stage_height = stage_height

        super().__init__(*args, **kwargs)

    @property
    def stage(self):
        return ceil(self.position / self._stage_height)

    def near_drop_stage(self):
        """Ближайший этаж, на котором нужно высадить пассажира"""

        cur_stage = self.stage()
        if self.passengers:
            _, stage = min([(abs(cur_stage - x.need_stage), x.need_stage)
                            for x in self.passengers],
                           lambda x: x[0])

            return stage

        return cur_stage

    def stop(self):
        self.status = LiftStatus.STOPPED


class Actor(Schema):
    uid = fields.Str(required=True)
    weight = fields.Float(required=True)
    stage = fields.Int(default=1, missing=1, allow_none=True)
    need_stage = fields.Int(default=None, missing=None, allow_none=True)
    status = EnumField(ActorStatus, load_by=EnumField.VALUE,
                       default=ActorStatus.SLEEP, missing=ActorStatus.SLEEP)
    timestamp = fields.DateTime(ISO8601_FORMAT, missing=lambda: dt.utcnow())
