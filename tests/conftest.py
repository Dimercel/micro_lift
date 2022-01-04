import pytest

from sanic.app import Sanic
from sanic.websocket import WebSocketProtocol

from micro_lift.main import init_app


Sanic.test_mode = True

@pytest.fixture
def cli(loop, sanic_client):
    app = init_app('config/config.yaml')

    return loop.run_until_complete(sanic_client(app, scheme='ws', protocol=WebSocketProtocol))
