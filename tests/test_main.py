import pytest
import ujson


async def test_auth(cli):
    conn = await cli.ws_connect('/ws')
    await conn.send(ujson.dumps({'signal': 'auth', 'data': {}}))
    msg = await conn.recv()
    await conn.close()
