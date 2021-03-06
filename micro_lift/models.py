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
        self._position = 0.01
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

    def near_act_floor(self, actors):
        """Ближайший этаж на котором нужно выполнить какое-то действие"""

        drop, take = self._near_drop_floor(), self._near_take_floor(actors)

        if None not in (drop, take):
            return drop if abs(self.floor - drop) < abs(self.floor - take) else take

        return drop or take

    def drop_off(self):
        """Высаживаем пассажиров, которые должны выйти на этом этаже"""

        drop_off = self._out_passengers()
        for p in drop_off:
            self._passengers.remove(p)
            p.leave_lift()

        return drop_off

    def take_actors(self, actors):
        """Забирает actor'ов c текущего этажа, если им нужен лифт"""

        new_passengers = [x for x in actors if x.floor == self.floor and
                          x.status == ActorStatus.EXPECT]

        # теперь нужно проверить ограничение с грузоподъемностью лифта
        new_passengers.sort(key=lambda x: x.weight)
        possible_weight = self._max_weight - sum([x.weight for x in self._passengers])
        extra_inx = weight = 0
        for p in new_passengers:
            extra_inx += 1
            if possible_weight > weight + p.weight:
                break

            weight += p.weight

        new_passengers = new_passengers[0:extra_inx]
        for x in new_passengers:
            x.enter_lift()

        self._passengers += new_passengers

        return new_passengers

    def stop(self):
        self._status = LiftStatus.STOPPED

    def move_to_act_floor(self, actors):
        """Перемещает лифт на один шаг к ближайшему этажу с посадкой/высадкой"""

        near = self.near_act_floor(actors)
        if near is not None:
            if near < self.floor:
                self.move_down()
            else:
                self.move_up()

    def move_up(self):
        self._status = LiftStatus.IN_ACTION
        self._position += self._speed

    def move_down(self):
        self._status = LiftStatus.IN_ACTION
        self._position -= self._speed

        if self._position < 0:
            self._position = 0

    def is_empty(self):
        return not self._passengers

    def _out_passengers(self):
        """Пассажиры, выходящие на текущем этаже"""

        return [x for x in self._passengers if x.need_floor == self.floor]

    def _near_drop_floor(self):
        """Ближайший этаж, на котором нужно высадить пассажира"""

        cur_floor = self.floor
        dist = [(abs(cur_floor - x.need_floor), x.need_floor) for x in self._passengers]

        return min(dist, key=lambda x: x[0])[1] if dist else None

    def _near_take_floor(self, actors):
        """Ближайший этаж, на котором следует забрать пассажира,
        при условии что его вес не приведет к перегрузке лифта
        """
        cur_floor = self.floor
        possible_weight = self._max_weight - sum([x.weight for x in self._passengers])
        dist = [(abs(cur_floor - x.floor), x.floor) for x in actors
                if x.weight <= possible_weight and x.status == ActorStatus.EXPECT]

        return min(dist, key=lambda x: x[0])[1] if dist else None



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

    @floor.setter
    def floor(self, value):
        if value >= 1:
            self._floor = value

    @property
    def need_floor(self):
        return self._need_floor

    @property
    def status(self):
        return self._status

    @property
    def timestamp(self):
        return self._timestamp

    def idle(self):
        """Переход в режим бездействия"""
        if self._status == ActorStatus.EXPECT:
            self._status = ActorStatus.IDLE
            self._need_floor = None

    def wait_lift(self, floor):
        """Ожидать лифт на текущем этаже"""
        if self._status != ActorStatus.IN_LIFT and floor != self._floor:
            self._need_floor = floor
            self._status = ActorStatus.EXPECT

    def leave_lift(self):
        """Покидает лифт и выходит на этаж"""

        if self._status == ActorStatus.IN_LIFT:
            self._status = ActorStatus.IDLE
            self._need_floor = None

            return True

        return False

    def enter_lift(self):
        """Заходит в лифт, если это возможно"""

        if self._status == ActorStatus.EXPECT:
            self._status = ActorStatus.IN_LIFT

            return True

        return False
