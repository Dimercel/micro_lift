import argparse
import sys

from sanic import Sanic

from conf import load_config

from models import Lift
from views import LiftApp


def init_app(config_path):
    app = Sanic("Lift app")
    config = load_config(config_path)
    app.config.update(config)

    app.ctx.actors = {}
    app.ctx.lifts = {}
    for inx in range(config['LIFT_COUNT']):
        app.ctx.lifts[f'lift_{inx}'] = Lift(
            f'lift_{inx}',
            config['LIFT_SPEED'],
            config['LIFT_MAX_WEIGHT'],
            config['FLOOR_HEIGHT']
        )

    app.ctx.sockets = {}
    app.ctx.by_ws = {}

    lift_app = LiftApp(app)

    app.add_websocket_route(lift_app.entry_point, '/ws')
    app.add_task(lift_app.lift_loop)

    return app


def main():
    parser = argparse.ArgumentParser(description='Lift app')
    parser.add_argument('--config', type=str, help='Path to configuration yaml file')
    args = parser.parse_args()

    app = init_app(args.config)
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        unix=app.config['UNIX'],
        debug=app.config['DEBUG'],
        sock=app.config['SOCK'],
        workers=app.config['WORKERS'],
        access_log=app.config['ACCESS_LOG']
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
