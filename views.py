import json

import ujson

from auth import gen_token
from schema import AuthSchema
from schema import with_schema


class LiftApp:
    def __init__(self, app):
        self.ws = None
        self.app = app
        self.actor = None

        self._ROUTES = {
            'auth': self._auth_actor,
        }

    def route(self, action):
        return self._ROUTES.get(action)

    async def entry_point(self, request, ws):
        self.ws = ws

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            action = data['action']

            handler = self.route(action)
            await handler(action, data['data'])

    @with_schema(AuthSchema)
    async def _auth_actor(self, action, data):
        await self.ws.send(self._response(action, {'test': 'ok'}))

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
