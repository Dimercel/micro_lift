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

    def route(self, action):
        return self._ROUTES.get(action)

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
                actor = Actor().load({
                    'uid': uid,
                    'weight': data['weight'],
                })

        return actor

    async def entry_point(self, request, ws):

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            action = data['action']
            try:
                handler = self.route(action)
                await handler(action, data['data'], request, ws)
            except TokenExpired as e:
                await ws.send(self._error(action, 403, str(e)))
                continue
            except Exception as e:
                await ws.send(self._error(action, 400, str(e)))
                break

    @with_schema(sc.AuthSchema)
    async def _auth_actor(self, action, data, req, ws):
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

            await ws.send(self._response(action, Actor().dump(actor)))
        else:
            await ws.send(self._error(action, 403, 'Forbidden request'))
            await ws.close()

    @with_schema(sc.LiftListSchema)
    async def _lift_list(self, action, data, req, ws):
        lifts = list(self.app.ctx.lifts.values())

        await ws.send(self._response(
            action, Lift().dump(lifts[:data['count']], many=True)))

    @with_schema(sc.ActorListSchema)
    async def _actor_list(self, action, data, req, ws):
        actors = list(self.app.ctx.actors.values())

        await ws.send(self._response(
            action, Actor().dump(actors[:data['count']], many=True)))

    async def _actor_sleep(self, action, data, req, ws):
        actor = self.app.ctx.by_ws.get(ws)

        if actor['status'] == ActorStatus.EXPECT:
            actor['status'] = ActorStatus.SLEEP
            actor['need_stage'] = None

            await ws.send(self._response(action, Actor().dump(actor)))

    @with_schema(sc.ActorExpectSchema)
    async def _actor_expect(self, action, data, req, ws):
        actor = self.app.ctx.by_ws.get(ws)

        if actor['status'] == ActorStatus.SLEEP:
            actor['status'] = ActorStatus.EXPECT
            actor['need_stage'] = data['stage']

            await ws.send(self._response(action, Actor().dump(actor)))

    async def lift_loop(self, app):
        delay = app.config['LOOP_DELAY']

        while True:
            for lid, lift in app.ctx.lifts.items():
                if lift['status'] == LiftStatus.IN_ACTION:
                    if lift.stage == lift.near_drop_stage():
                        lift.stop()
                        await self._send_broadcast(
                            self._notify('lift_stop', {'stage': lift.stage}),
                            only=[x.uid for x in lift.passengers]
                        )

            await asyncio.sleep(delay)

    async def _send_broadcast(self, message, only=None):
        uids = self.app.ctx['sockets'].keys() if only is None else only
        for uid_item in uids:
            for sock in self.app.ctx['sockets'][uid_item]:
                await sock.send(message)

    @staticmethod
    def _response(route, data, status='ok'):
        return ujson.dumps({
            'type': 'response',
            'route': route,
            'status': status,
            'data': data
        })

    @classmethod
    def _error(cls, route, code, message):
        return cls._response(
            route,
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
