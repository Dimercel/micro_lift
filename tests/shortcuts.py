from datetime import datetime as dt

import ujson

from auth import gen_token


async def req(ws, signal, data, id='my_id'):
    await ws.send(ujson.dumps({'signal': signal, 'data': data, 'id': id}))


async def receive(*args):
    result = []
    for ws in args:
        data = await ws.recv()
        result.append(ujson.loads(data))

    if len(result) == 1:
        return result[0]

    return tuple(result)


async def ws_conn(client):
    return await client.ws_connect('/ws')


def quick_auth(app, uid, weight=70.0):
    timestamp = dt.utcnow().strftime(app.config['DATETIME_FORMAT'])

    return {
        'uid': uid,
        'token': gen_token(app.config['SECRET_KEY'], uid, timestamp),
        'timestamp': timestamp,
        'weight': weight
    }


async def auth_actors(client, *uids):
    sockets = []

    for uid_item in uids:
        ws = await ws_conn(client)
        await req(ws, 'auth', quick_auth(client.app, uid_item))
        await receive(ws)

        sockets.append(ws)

    return tuple(sockets)
