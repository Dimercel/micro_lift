import pytest

from sanic.websocket import WebSocketProtocol

from main import init_app


@pytest.fixture
def cli(loop, sanic_client):
    app = init_app('config/config.yaml')

    return loop.run_until_complete(sanic_client(app, scheme='ws', protocol=WebSocketProtocol))
