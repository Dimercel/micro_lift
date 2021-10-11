import asyncio
from datetime import datetime as dt
import json

import ujson

from auth import is_expired_token, is_valid_auth
from models import Actor, Lift, ActorStatus, LiftStatus
from schema import with_schema
import schema as sc


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
            'actor_sleep': self._actor_sleep,
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
            data = json.loads(msg)

            signal = data['signal']
            try:
                handler = self.route(signal)
                if handler is None:
                    await ws.send(self._error(signal, 404, str('Signal not found!')))
                    continue

                await handler(signal, data['data'], request, ws)
            except TokenExpired as e:
                await ws.send(self._error(signal, 403, str(e)))
                continue
            except Exception as e:
                await ws.send(self._error(signal, 400, str(e)))
                break

    @with_schema(sc.AuthSchema)
    async def _auth_actor(self, signal, data, req, ws):
        uid = data['uid']
        ctx = self.app.ctx

        actor = self.authenticate(data)
        if actor:
            ctx.actors[uid] = actor
            ctx.by_ws[ws] = actor

            if uid in ctx.sockets and ctx.sockets[uid]:
                ctx.sockets[uid].append(ws)
            else:
                ctx.sockets[uid] = [ws]

            await ws.send(self._response(signal, sc.Actor().dump(actor)))
        else:
            await ws.send(self._error(signal, 403, 'Forbidden request'))
            await ws.close()

    @with_schema(sc.LiftListSchema)
    async def _lift_list(self, signal, data, req, ws):
        lifts = list(self.app.ctx.lifts.values())

        await ws.send(self._response(
            signal, sc.Lift().dump(lifts[:data['count']], many=True)))

    @with_schema(sc.ActorListSchema)
    async def _actor_list(self, signal, data, req, ws):
        actors = list(self.app.ctx.actors.values())

        await ws.send(self._response(
            signal, sc.Actor().dump(actors[:data['count']], many=True)))

    async def _actor_sleep(self, signal, data, req, ws):
        actor = self.app.ctx.by_ws.get(ws)

        # TODO сделать в соответствии с моделью Actor
        if actor.status == ActorStatus.EXPECT:
            actor['status'] = ActorStatus.SLEEP
            actor['need_floor'] = None

        await ws.send(self._response(signal, sc.Actor().dump(actor)))

    @with_schema(sc.ActorExpectSchema)
    async def _actor_expect(self, signal, data, req, ws):
        actor = self.app.ctx.by_ws.get(ws)

        if actor.status != ActorStatus.IN_LIFT:
            actor.wait_lift(data['floor'])

        await ws.send(self._response(signal, sc.Actor().dump(actor)))

    async def lift_loop(self, app):
        delay = app.config['LOOP_DELAY']

        while True:
            for id, lift in app.ctx.lifts.items():
                if lift.status == LiftStatus.IN_ACTION:
                    if lift.floor == lift.near_drop_floor():
                        lift.stop()
                        await self._send_broadcast(
                            self._notify('lift_stop', {'floor': lift.floor}),
                            only=[x.uid for x in lift.passengers]
                        )

                elif lift.status == LiftStatus.STOPPED:
                    if lift.passengers:
                        out_pass = lift.out_passengers()
                        if out_pass:
                            # Высаживаем пассажиров
                            lift.passengers = [x for x in lift.passengers if x not in out_pass]

                            for passenger in out_pass:
                                passenger.leave_lift()

            await asyncio.sleep(delay)

    async def _send_broadcast(self, message, only=None):
        uids = self.app.ctx['sockets'].keys() if only is None else only
        for uid_item in uids:
            for sock in self.app.ctx['sockets'][uid_item]:
                await sock.send(message)

    @staticmethod
    def _response(signal, data, status='ok'):
        return ujson.dumps({
            'type': 'response',
            'signal': signal,
            'status': status,
            'data': data
        })

    @classmethod
    def _error(cls, signal, code, message):
        return cls._response(
            signal,
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
