from marshmallow import Schema, fields
import yaml


class ConfigSchema(Schema):
    HOST = fields.Str(required=True)
    PORT = fields.Int(required=True)
    UNIX = fields.Str(missing=None, allow_none=True)
    DEBUG = fields.Bool(default=False, missing=False)
    SOCK = fields.Str(missing=None, allow_none=True)
    WORKERS = fields.Int(default=1)
    ACCESS_LOG = fields.Bool(default=False, missing=False)

    SECRET_KEY = fields.Str(required=True)


def load_config(config_path):
    config = {}
    with open(config_path, 'rt') as fconf:
        data = yaml.load(fconf, Loader=yaml.FullLoader)
        config = ConfigSchema().load(data)

    return config
