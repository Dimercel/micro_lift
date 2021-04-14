from marshmallow import Schema, fields
import yaml


class ConfigSchema(Schema):
    host = fields.Str(required=True)
    port = fields.Int(required=True)
    unix = fields.Str(missing=None, allow_none=True)
    debug = fields.Bool(default=False, missing=False)
    sock = fields.Str(missing=None, allow_none=True)
    workers = fields.Int(default=1)
    access_log = fields.Bool(default=False, missing=False)


def load_config(config_path):
    config = {}
    with open(config_path, 'rt') as fconf:
        data = yaml.load(fconf, Loader=yaml.FullLoader)
        config = ConfigSchema().load(data)

    return config
