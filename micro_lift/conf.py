from marshmallow import Schema, fields
import yaml


class FloorSchema(Schema):
    COUNT = fields.Int(required=True)
    HEIGHT = fields.Float(required=True)

class LiftSchema(Schema):
    COUNT = fields.Int(required=True)
    MAX_WEIGHT = fields.Float(default=300.0, missing=300.0)
    SPEED = fields.Float(default=0.25, missing=0.25)

class ConfigSchema(Schema):
    HOST = fields.Str(required=True)
    PORT = fields.Int(required=True)
    UNIX = fields.Str(missing=None, allow_none=True)
    DEBUG = fields.Bool(default=False, missing=False)
    SOCK = fields.Str(missing=None, allow_none=True)
    WORKERS = fields.Int(default=1)
    ACCESS_LOG = fields.Bool(default=False, missing=False)

    AUTH_TOKEN_DELAY = fields.Int(required=True)
    DATETIME_FORMAT = fields.Str(required=True)
    FLOOR = fields.Nested(FloorSchema, required=True)
    LIFT = fields.Nested(LiftSchema, required=True)
    LOOP_DELAY = fields.Float(required=True)
    SECRET_KEY = fields.Str(required=True)


def load_config(config_path):
    config = {}
    with open(config_path, 'rt') as fconf:
        data = yaml.load(fconf, Loader=yaml.FullLoader)
        config = ConfigSchema().load(data)

    return config
