import asyncio
from datetime import datetime as dt
from functools import wraps

from marshmallow.exceptions import ValidationError
import ujson

from auth import is_expired_token, is_valid_auth
from models import Actor, ActorStatus, LiftStatus
from schema import with_schema
import schema as sc


class AuthRequired(Exception):
    def __init__(self, message='Unauthorized request', *args, **kwargs):
        super().__init__(message, *args, **kwargs)


def auth_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        ws = args[-1]

        if self.app.ctx.by_ws.get(ws) is None:
            raise AuthRequired

        return func(self, *args, **kwargs)

    return wrapper


class TokenExpired(Exception):
    def __init__(self, message='Token is expired', *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class LiftApp:
    def __init__(self, app):
        self.app = app

        self._ROUTES = {
            'auth': self._auth_actor,
            'lift_list': self._lift_list,
            'actor_list': self._actor_list,
            'actor_idle': self._actor_idle,
            'actor_expect': self._actor_expect,
        }

    def route(self, signal):
        return self._ROUTES.get(signal)

    def authenticate(self, data):
        uid, conf, actor = data['uid'], self.app.config, None
        ctx = self.app.ctx

        token_timestamp = dt.strptime(data['timestamp'], conf['DATETIME_FORMAT'])
        if is_expired_token(token_timestamp, conf['AUTH_TOKEN_DELAY']):
            raise TokenExpired

        actor = None
        if is_valid_auth(data, conf['SECRET_KEY']):
            actor = ctx.actors.get(uid)
            if not actor:
                actor = Actor(uid, data['weight'])

        return actor

    async def entry_point(self, request, ws):

        while True:
            msg = await ws.recv()
            try:
                data = ujson.loads(msg)
                # Предварительная валидация сообщения в соответствии с протоколом
                valid_data = sc.IncomingSchema().load(data)
            except ValueError as e:
                await ws.send(self._error('invalid', None, 400, str(e)))
                continue
            except ValidationError as e:
                await ws.send(self._error('invalid', data.get(id), 400, str(e)))
                continue

            signal, id = valid_data['signal'], valid_data['id']
            try:
                handler = self.route(signal)
                if handler is None:
                    await ws.send(self._error(signal, id, 404, str('Signal not found!')))
                    continue

                await handler(signal, id, data['data'], request, ws)
            except AuthRequired as e:
                await ws.send(self._error(signal, id, 401, str(e)))
                continue
            except TokenExpired as e:
                await ws.send(self._error(signal, id, 403, str(e)))
                continue
            except Exception as e:
                await ws.send(self._error(signal, id, 400, str(e)))
                break

    @with_schema(sc.AuthSchema)
    async def _auth_actor(self, signal, id, data, req, ws):
        """Аутентифицирует нового актора в сервисе"""

        uid = data['uid']
        ctx = self.app.ctx

        actor = self.authenticate(data)
        if actor:
            ctx.actors[uid] = actor
            ctx.by_ws[ws] = actor

            if uid in ctx.sockets and ctx.sockets[uid]:
                ctx.sockets[uid].add(ws)
            else:
                ctx.sockets[uid] = {ws}

            await self._send_broadcast(
                self._notify('actor_arrive', sc.Actor().dump(actor)),
                exclude={uid}
            )
            await ws.send(self._response(signal, id, sc.Actor().dump(actor)))
        else:
            await ws.send(self._error(signal, id, 403, 'Forbidden request'))
            await ws.close()

    @auth_required
    @with_schema(sc.LiftListSchema)
    async def _lift_list(self, signal, id,  data, req, ws):
        """Выводит список всех лифтов в здании"""

        lifts = list(self.app.ctx.lifts.values())
        await ws.send(self._response(
            signal, id, sc.Lift().dump(lifts[:data['count']], many=True)))

    @auth_required
    @with_schema(sc.ActorListSchema)
    async def _actor_list(self, signal, id, data, req, ws):
        """Выводит список всех подключенных акторов"""

        actors = list(self.app.ctx.actors.values())
        await ws.send(self._response(
            signal, id, sc.Actor().dump(actors[:data['count']], many=True)))

    @auth_required
    async def _actor_idle(self, signal, data, req, ws):
        """Переводит актора в режим бездействия"""

        actor = self.app.ctx.by_ws.get(ws)

        # TODO сделать в соответствии с моделью Actor
        if actor.status == ActorStatus.EXPECT:
            actor['status'] = ActorStatus.IDLE
            actor['need_floor'] = None

        await ws.send(self._response(signal, id, sc.Actor().dump(actor)))

    @auth_required
    @with_schema(sc.ActorExpectSchema)
    async def _actor_expect(self, signal, id, data, req, ws):
        """Устанавливает желаемый этаж для поезди актору"""
        actor = self.app.ctx.by_ws.get(ws)

        if actor.status != ActorStatus.IN_LIFT:
            actor.wait_lift(data['floor'])

        await ws.send(self._response(signal, id, sc.Actor().dump(actor)))

    async def lift_loop(self, app):
        """Петля действий для лифта"""

        delay = app.config['LOOP_DELAY']
        actors = app.ctx.actors.values()

        while True:
            for lift_id, lift in app.ctx.lifts.items():
                near = lift.near_act_floor(actors)
                if lift.status == LiftStatus.IN_ACTION:
                    cur_floor = lift.floor
                    for p in lift.passengers:
                        p.floor = cur_floor

                    if near is None or lift.floor == near:
                        lift.stop()
                    else:
                        lift.move_to_act_floor(actors)

                elif lift.status == LiftStatus.STOPPED:
                    if near is not None and lift.floor == near:
                        # Сначала высаживаем
                        await self._send_broadcast(
                            self._notify('drop_off', {'id': lift_id, 'floor': lift.floor}),
                            only=[x.uid for x in lift.drop_off()]
                        )

                        # Потом забираем, если это необходимо
                        await self._send_broadcast(
                            self._notify('enter_lift', {'id': lift_id, 'floor': lift.floor}),
                            only=[x.uid for x in lift.take_actors(actors)]
                        )

                        lift.move_to_act_floor(actors)

                    if near is not None and lift.floor != near:
                        lift.move_to_act_floor(actors)

            await asyncio.sleep(delay)

    async def _send_broadcast(self, message, only=None, exclude=[]):
        """Широковещательная посылка сообщений акторам"""
        uids = self.app.ctx.sockets.keys() if only is None else only
        for uid_item in uids:
            if uid_item not in exclude:
                for sock in self.app.ctx.sockets[uid_item]:
                    await sock.send(message)

    @staticmethod
    def _response(signal, id, data, status='ok'):
        return ujson.dumps({
            'type': 'response',
            'signal': signal,
            'id': id,
            'status': status,
            'data': data
        })

    @classmethod
    def _error(cls, signal, id,  code, message):
        return cls._response(
            signal,
            id,
            {'code': code, 'message': message},
            'error'
        )

    @staticmethod
    def _notify(event, data):
        return ujson.dumps({
            'type': 'notify',
            'event': event,
            'data': data
        })
