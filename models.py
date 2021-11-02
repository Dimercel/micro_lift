from datetime import datetime as dt
from enum import Enum
from math import ceil


ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class LiftStatus(Enum):
    STOPPED = 0

    IN_ACTION = 1


class ActorStatus(Enum):
    IDLE = 0
    EXPECT = 1
    IN_LIFT = 2


class Lift():
    def __init__(self, id, speed, max_weight, floor_height=1.0, *args, **kwargs):
        self._id = id
        self._speed = speed
        self._max_weight = max_weight
        self._position = 0.0
        self._passengers = []
        self._status = LiftStatus.STOPPED
        self._floor_height = floor_height

        super().__init__(*args, **kwargs)

    @property
    def id(self):
        return self._id

    @property
    def speed(self):
        return self._speed

    @property
    def max_weight(self):
        return self._max_weight

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        if pos >= 0.0:
            self._position = pos

    @property
    def passengers(self):
        return self._passengers

    @passengers.setter
    def passengers(self, pas):
        if sum([x.weight for x in pas]) <= self._max_weight:
            self._passengers = pas

    @property
    def status(self):
        return self._status

    @property
    def floor(self):
        return ceil(self.position / self._floor_height)

    def near_drop_floor(self):
        """Ближайший этаж, на котором нужно высадить пассажира"""

        cur_floor = self.floor
        dist = [(abs(cur_floor - x.need_floor), x.need_floor) for x in self.passengers]
        return min(dist, key=lambda x: x[0])[1] if dist else None

    def near_take_floor(self, actors):
        """Ближайший этаж, на котором следует забрать пассажира"""

        cur_floor = self.floor
        dist = [(abs(cur_floor - x.floor), x.floor) for x in actors]
        return min(dist, key=lambda x: x[0])[1] if dist else None


    def stop(self):
        self._status = LiftStatus.STOPPED

    def move_up(self):
        self._status = LiftStatus.IN_ACTION
        self._position += self.speed

    def move_down(self):
        self._status = LiftStatus.IN_ACTION
        self._position -= self.speed

        if self._position < 0:
            self._position = 0

    def out_passengers(self):
        return [x for x in self._passengers if x.need_floor == self.floor]

    def is_empty(self):
        return not self._passengers


class Actor:
    def __init__(self, uid, weight):
        self._uid = uid
        self._weight = weight
        self._floor = 1
        self._need_floor = None
        self._status = ActorStatus.IDLE
        self._timestamp = dt.utcnow()

    @property
    def uid(self):
        return self._uid

    @property
    def weight(self):
        return self._weight

    @property
    def floor(self):
        return self._floor

    @property
    def need_floor(self):
        return self._need_floor

    @property
    def status(self):
        return self._status

    @property
    def timestamp(self):
        return self._timestamp

    def wait_lift(self, floor):
        if floor != self._floor:
            self._need_floor = floor
            self._status = ActorStatus.EXPECT

    def leave_lift(self):
        if self._floor == self._need_floor:
            self._status = ActorStatus.IDLE
            self._need_floor = None

        return self._floor
