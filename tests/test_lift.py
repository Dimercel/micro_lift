from datetime import datetime as dt
from datetime import timedelta

from .shortcuts import req, receive, ws_conn, auth_actors
from auth import gen_token
from schema import ISO8601_FORMAT


async def test_bad_token(cli):
    """Тест на попытку аутентификации с неверным токеном"""

    ws = await ws_conn(cli)

    timestamp = dt.utcnow().strftime(ISO8601_FORMAT)
    await req(ws, 'auth', {
        'uid': 'actor1',
        'token': gen_token(cli.app.config['SECRET_KEY'], 'bad_uid', timestamp),
        'timestamp': timestamp,
        'weight': 70.0
    })

    resp = await receive(ws)
    assert resp['status'] == 'error'


async def test_expired_token(cli):
    """Токен для аутентификации выдается на определенный интервал
    времени, по истечении которого становится недействительным.
    При истекшем токене не должно быть успешной аутентификации
    """

    ws = await ws_conn(cli)

    delay = cli.app.config['AUTH_TOKEN_DELAY']
    past_timestamp = (dt.utcnow() - timedelta(seconds=delay * 2)).strftime(ISO8601_FORMAT)
    expired_auth = {
        'uid': 'actor1',
        'token': gen_token(cli.app.config['SECRET_KEY'], 'actor1', past_timestamp),
        'timestamp': past_timestamp,
        'weight': 70.0
    }

    await req(ws, 'auth', expired_auth)

    resp = await receive(ws)
    assert resp['status'] == 'error'


async def test_not_change_status_in_lift(cli):
    """Тестирует невозможность переключения статуса актора внутри лифта"""
    ws,  = await auth_actors(cli, 'actor1')
    await req(ws, 'actor_expect', {'floor': 10})

    resp = await receive(ws)
    assert resp['status'] == 'ok'

    resp = await receive(ws)
    assert resp['type'] == 'notify'
    assert resp['event'] == 'enter_lift'

    # Актор зашел в лифт и теперь не может перейти в режим "бездействия"
    await req(ws, 'actor_idle', {})

    resp = await receive(ws)
    assert resp['data']['status'] != 'IDLE'

    # Актор зашел в лифт и теперь не может перейти в режим "ожидания"
    await req(ws, 'actor_expect', {'floor': 9})

    resp = await receive(ws)
    assert resp['data']['status'] != 'EXPECT'
