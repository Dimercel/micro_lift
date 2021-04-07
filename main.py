import sys

from sanic import Sanic
from sanic.response import json
import asyncio

from views import LiftApp

app = Sanic("Lift app")


def main():
    lift_app = LiftApp()

    app.add_websocket_route(lift_app.entry_point, '/ws')
    app.run()

    return 0

if __name__ == '__main__':
    sys.exit(main())
