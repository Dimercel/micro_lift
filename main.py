import argparse
import sys

from sanic import Sanic
import asyncio

from conf import load_config

from models import Lift
from views import LiftApp

app = Sanic("Lift app")


def main():
    parser = argparse.ArgumentParser(description='Lift app')
    parser.add_argument('--config', type=str, help='Path to configuration yaml file')
    args = parser.parse_args()

    config = load_config(args.config)
    app.config.update(config)

    app.ctx.actors = {}
    app.ctx.lifts = {}
    for inx in range(config['LIFT_COUNT']):
        app.ctx.lifts[f'lift_{inx}'] = Lift().load({
            'id': f'lift_{inx}',
            'speed': 1.0,
            'max_weight': 300,
        })

    app.ctx.sockets = {}

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
