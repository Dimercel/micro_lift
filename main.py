import argparse
import sys

from sanic import Sanic
from sanic.response import json
import asyncio

from conf import load_config

from views import LiftApp

app = Sanic("Lift app")


def main():
    parser = argparse.ArgumentParser(description='Lift app')
    parser.add_argument('--config', type=str, help='Path to configuration yaml file')
    args = parser.parse_args()

    config = load_config(args.config)
    app.config.update(config)

    lift_app = LiftApp(app)

    app.add_websocket_route(lift_app.entry_point, '/ws')
    app.run(
        host=config['HOST'],
        port=config['PORT'],
        unix=config['UNIX'],
        debug=config['DEBUG'],
        sock=config['SOCK'],
        workers=config['WORKERS'],
        access_log=config['ACCESS_LOG']
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
